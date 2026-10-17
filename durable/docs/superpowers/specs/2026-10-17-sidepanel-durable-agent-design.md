# BabySteps side-panel agent (pi-durable in a Chrome extension)

Date: 2026-10-17
Status: draft, awaiting approval

## Intent

BabySteps helps an older person get through confusing online tasks: a Berlin Bürgeranmeldung, changing a setting in Google Photos, and other bureaucratic or settings chores. An agent sits next to the page and **guides**: it reads what is on the page and points at what to do next, for example by making the right button glow. The person still does the clicking.

These tasks are interrupted constantly (closed tab, closed panel, a pause to fetch a document), so the agent must not lose its place. That is why it is built on [`@earendil-works/pi-durable`](https://www.npmjs.com/package/@earendil-works/pi-durable): every turn and tool call is committed to storage before it is shown, and an unfinished run resumes after reopening.

This folder (`BabySteps/durable/`) answers the question "can a pi-durable agent run entirely inside the browser?" by building it as a Chrome extension. The extension is meant to grow into BabySteps' extension; more page-pointing features will be added later.

## Goals

1. A Chrome extension (Manifest V3) whose agent UI lives in Chrome's side panel (`chrome.sidePanel`).
2. **One agent per browser tab.** Each tab gets its own conversation, its own pi-durable `Harness`, and its own database.
3. **Everything local.** Conversation state lives in SQLite compiled to WebAssembly, stored in the extension's Origin Private File System (OPFS). No server, no proxy, no central service.
4. The model is Claude, called directly from the browser with an API key the user pastes into the panel.
5. Two kinds of tools against the tab the panel belongs to:
   - `read_page`: a compact text snapshot of the visible, interactive parts of the page, each element tagged with a short id.
   - `highlight` (glow an element by id, optionally with a short label) and `clear_highlights`.
6. Durability you can see: close and reopen the side panel (or reload the extension) mid-conversation, and the transcript is still there and an interrupted run continues.

## Non-goals (for now)

- Acting on the page (clicking, typing, submitting). Guiding only.
- A background service, shared agent across tabs, or any cross-tab coordination.
- Agent keeps running while the side panel is closed. It pauses; reopening resumes.
- Keeping a tab's conversation across a full browser restart (tab ids change on restart; see Open risks).
- Proxying or hiding the API key; multi-user; publishing to the Chrome Web Store.
- Code mode, `bash`/`read`/`write`/`edit`, image processing (Photon). None of these are needed for guiding.
- Polished UI. A plain, legible chat is enough.

## Anti-goals (failure even if it "works")

- Any conversation data or page content sent anywhere except the Anthropic API.
- The agent clicking or typing on the user's behalf.
- Losing a conversation when the panel is closed and reopened.
- Two panels writing to the same database (pi-durable has no cross-process locking; this would corrupt state).

## Constraints

- pi-durable is experimental and its API changes without notice. Pin exact versions (`@earendil-works/pi-durable`, `@earendil-works/pi-ai`, `@earendil-works/chord` at `1.3.0`) via the lockfile.
- Chrome Manifest V3. WebAssembly in extension pages requires `'wasm-unsafe-eval'` in `content_security_policy.extension_pages`.
- Use the repo's own Chrome (`../scripts/chrome.sh`, Chrome for Testing) for manual testing; load unpacked.
- Node ≥ 22.19 for the build toolchain (pi-durable's `engines`).

## How it works (decided)

These were checked against the published 1.3.0 packages:

- **pi-durable, pi-ai and chord are browser-safe** outside their `*/node` entry points (no `node:`/`fs`/`path` imports in the core). Use the portable `SqliteStorage` from `@earendil-works/pi-durable/storage/sqlite`, never `storage/sqlite/node`.
- **pi-ai's Anthropic provider already supports the browser**: it sets `dangerouslyAllowBrowser` and the `anthropic-dangerous-direct-browser-access` header, and accepts a stored credential (`{ type: "api_key", key }`) instead of environment variables.
- **The agent is plain JavaScript; WASM runs the database.** pi-durable needs only an async `SqliteDatabase` facade (`exec`, `run`, `get`, `all`, `transaction`, `close`; see `dist/storage/sqlite/database.d.ts`). Its async shape fits a worker boundary.

### Architecture

```
Chrome window
├── Tab N (web page)
│     └── injected content script: page snapshot + glow overlay
└── Side panel for tab N  (panel.html?tab=N)   ← one document per tab
      ├── chat UI
      ├── pi-durable Harness (main thread)
      │     ├── models: pi-ai anthropicProvider, key from chrome.storage.local
      │     ├── registry: BabySteps extension (system prompt + tools)
      │     └── storage: SqliteStorage(WorkerSqliteDatabase)
      └── Dedicated Worker
            └── @sqlite.org/sqlite-wasm, opfs-sahpool VFS, pool dir per tab
```

- **Side panel per tab.** The background service worker does only setup: on action click it calls `chrome.sidePanel.setOptions({ tabId, path: "panel.html?tab=<tabId>", enabled: true })` and `chrome.sidePanel.open({ tabId })`. It holds no agent state. The panel reads its tab id from the query string.
- **Storage per tab.** The panel spawns a dedicated Worker running SQLite-WASM with the `opfs-sahpool` VFS (works without COOP/COEP headers). Each tab uses its own pool directory/database, so two panels never share a database. *(My call)* The database key is `<browserSessionId>-<tabId>`, where `browserSessionId` is a random id created once per browser session and kept in `chrome.storage.session`. Chrome reuses tab ids after a restart, so a bare tab id could open a stranger's old conversation in a new tab.
- **One conversation per tab, with "start over".** *(My call)* Each tab has a single root conversation. A "New task" button in the panel calls pi-durable's reset on it, so the model starts fresh. Older entries stay in the database but are not shown to the model. The main thread talks to the worker through a small RPC that implements `SqliteDatabase`, including queueing other calls while a transaction is open, as the interface requires.
- **Harness lifecycle.** On panel load: open storage → `Harness.open(...)` → `harness.root(...)` (creates the conversation on first use) → render existing transcript → `harness.resume()`. On panel unload, close if possible; correctness must not depend on it (the next open resumes).
- **Tools** are defined with `defineTool` in one `defineExtension({ name: "babysteps", ... })`, plus a system-prompt `section` describing the job: patient, plain language, short steps, one thing at a time, point rather than explain abstractly, never claim to have clicked anything.
  - `read_page` → `chrome.scripting.executeScript` into this panel's tab. Returns visible interactive elements (links, buttons, inputs, selects, labels, headings) with role, accessible name/text, and a short id, which is also stamped on the element (for example a `data-babysteps-id` attribute) so `highlight` can find it again. Output is bounded in size.
  - `highlight({ id, label? })` → overlay glow (CSS outline/box-shadow pulse plus optional label bubble) on the element, scrolled into view. Fails with a clear message if the id is gone (page changed), so the model knows to call `read_page` again.
  - `clear_highlights()`.
  - All three are `replay: "safe"`: rerunning them after an interruption is harmless.
- **API key.** A settings field in the panel; stored in `chrome.storage.local`; passed to pi-ai as a stored credential. Never written into the transcript.
- **Permissions:** `sidePanel`, `scripting`, `storage`, `activeTab`, and host permissions `<all_urls>` (the person may be on any site).

### Relation to `BabySteps/extension/` (my call)

The existing `BabySteps/extension/` is a global side panel that talks to the Python server; its agent acts on the page. This extension is a **separate experiment** and replaces nothing:

- It lives entirely in `durable/` and runs in its own Chrome profile (`durable/.chrome-profile`, launched by a small script in `durable/` that reuses `../chrome/`), so its side panel and action button never compete with the old extension.
- It has its own guiding-only system prompt. It does not reuse `babysteps/prompt.py`, which is written for an agent that acts.
- The Musterstadt mock site exists only through the Python server's Playwright route interception. The extension ships its own static fake "Anmeldung einer Wohnung" form page as the test page instead.

### Tooling (my calls, open to change)

- TypeScript + Vite, building `panel.html`, the worker, the background service worker, and the injected script into `dist/`, which is loaded unpacked.
- npm, matching `~/IdeaProjects/pi-durable-work`.
- Model: Claude Sonnet (latest in pi-ai's Anthropic catalog). Thinking off or low; responses should be fast.

## Success check

Manual, in the repo's Chrome:

1. Load `dist/` unpacked, open a page with a form (a real Berlin service page or a local fake form), and click the extension action. The side panel opens for that tab.
2. Paste the API key. Type "help me fill in this form". The agent calls `read_page`, explains the first step in plain language, and the right field glows.
3. Close the side panel mid-answer and reopen it. The transcript is there, and the interrupted run either continues or the agent picks up sensibly.
4. Open a second tab, open its panel, and start a different conversation. Switch back: the first tab's conversation is unchanged.
5. The extension's OPFS contains one database per tab used; DevTools Network shows only `api.anthropic.com` traffic.

Automated: tests for the `SqliteDatabase` worker adapter using pi-durable's `registerStorageConformance` from `@earendil-works/pi-durable/testing`, run in a real browser (Vitest browser mode or equivalent), since OPFS doesn't exist in Node.

## Open risks for the builder to verify early

- **Side-panel document lifecycle per tab.** Confirm whether switching tabs keeps or destroys a tab-specific panel document. Either way is fine because durability covers it, but it affects how often the harness reopens.
- **opfs-sahpool exclusivity.** Each sahpool instance locks its pool. Confirm that per-tab pools in separate panel documents coexist, and that a panel reopened for the same tab can reacquire its pool after the old document is gone.
- **Bundle size / TypeBox.** pi-durable's root import pulls TypeBox (~4 MB in a tree-shaken bundle). Acceptable for an extension; note if it isn't.
- **Browser restart.** A new browser session id means a restored tab gets a fresh conversation and the old database is orphaned. Out of scope, but don't delete old databases; a later "continue a previous conversation" picker can use them.

## Left to the builder

- Exact page-snapshot format and element-selection heuristics, within a size bound.
- Glow styling, label bubble design, and how overlays are cleaned up on navigation.
- Chat UI details (streaming display via pi-durable's watch/events API, tool-call display).
- Folder layout inside `durable/`.
