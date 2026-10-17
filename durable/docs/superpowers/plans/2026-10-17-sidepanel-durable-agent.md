# BabySteps Side-Panel Durable Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A Manifest V3 Chrome extension where each tab's side panel runs its own pi-durable agent, stored in SQLite-WASM on OPFS, that guides the user by reading the page and making elements glow.

**Architecture:** The side panel page (`panel.html?tab=<id>`) hosts the pi-durable `Harness` on the main thread. A dedicated Worker runs `@sqlite.org/sqlite-wasm` with the `opfs-sahpool` VFS behind a promise-RPC that implements pi-durable's `SqliteDatabase`. Tools reach the tab through `chrome.scripting`, which injects a bundled page script exposing `window.__babysteps`. The background service worker only wires the action click to a per-tab panel.

**Tech Stack:** TypeScript, Vite (multi-entry build), Vitest (Node for pure logic, browser mode with Playwright on the repo's Chrome for OPFS/DOM tests), `@earendil-works/pi-durable@1.3.0`, `@earendil-works/pi-ai@1.3.0`, `@earendil-works/chord@1.3.0`, `@sqlite.org/sqlite-wasm`.

**Spec:** `docs/superpowers/specs/2026-10-17-sidepanel-durable-agent-design.md`

## Global Constraints

- All work lives in `BabySteps/durable/`. Do not touch `BabySteps/extension/` or the Python package.
- Pin `@earendil-works/pi-durable`, `@earendil-works/pi-ai`, `@earendil-works/chord` at exactly `1.3.0` (no `^`); commit `package-lock.json`.
- Never import any `*/node` entry point (`storage/sqlite/node`, `env/node`, `images/node`, `storage/jsonl/node`) or `@earendil-works/pi-durable/tools` / `codemode`.
- Manifest V3; `content_security_policy.extension_pages` = `"script-src 'self' 'wasm-unsafe-eval'; object-src 'self'"`.
- Permissions exactly: `sidePanel`, `scripting`, `storage`, `activeTab`; `host_permissions: ["<all_urls>"]`.
- Model: provider `anthropic`, modelId `claude-sonnet-5-5`, thinking level `off`.
- API key lives only in `chrome.storage.local` under key `anthropicApiKey`; never in a transcript entry or log.
- Database key per tab: `<browserSessionId>-<tabId>`; `browserSessionId` is a random UUID in `chrome.storage.session` under key `browserSessionId`.
- No network traffic except `api.anthropic.com`.
- Guide only: no tool clicks, types, or submits.
- Manual testing uses `durable/scripts/chrome.sh` (own profile `durable/.chrome-profile`, binary `../chrome/chrome`). Add `.chrome-profile/`, `node_modules/`, `dist/` to `durable/.gitignore`.
- Node ≥ 22.19.

## Review Focus

1. **Page navigates or re-renders between `read_page` and `highlight`.** The stale id must give the model an error result telling it to call `read_page` again, not throw from the tool or glow the wrong element. Pinned in Task 3 (`highlight returns not_found for a removed id`) and Task 4 (`highlight tool reports stale id as error result`).
2. **Pages where scripts can't be injected** (`chrome://` pages, the Chrome Web Store, PDF viewer). `read_page` must return a plain error result ("I can't see this kind of page"), and the panel must not crash. Pinned in Task 4 (`read_page tool turns injection failure into error result`).
3. **No or invalid API key.** The panel must show the key field and a readable message, not a stack trace or a run stuck on "thinking". Pinned in Task 5 (`settings: missing key blocks submit with message`); an invalid key surfaces as the run's `unanswered` reason, rendered as text (manual check in Task 6).
4. **Huge pages** (Google Photos settings, long forms). The snapshot must stay bounded so a request doesn't blow up. Pinned in Task 3 (`snapshot truncates to maxChars and says so`).
5. **Panel reopened while its old document still holds the sahpool lock.** Opening must retry briefly, then show "This tab's helper is open elsewhere", never open a second handle. Pinned in Task 1 (`second open of the same pool fails with PoolBusyError`) and handled in Task 5's open path.

---

## File Structure

```
durable/
  package.json, tsconfig.json, vite.config.ts, vitest.config.ts, vitest.browser.config.ts, .gitignore
  manifest.json                 # copied to dist by Vite (public/)
  scripts/chrome.sh             # launch repo Chrome with durable/.chrome-profile + --load-extension=dist
  src/
    db/protocol.ts              # RPC message types shared by worker and client
    db/sqlite-worker.ts         # Worker: sqlite-wasm + opfs-sahpool, executes RPC
    db/worker-database.ts       # Main thread: WorkerSqliteDatabase implements SqliteDatabase
    tab-key.ts                  # browserSessionId + databaseKey
    page/page-script.ts         # bundled IIFE injected into tabs: snapshot/highlight/clear
    page/bridge.ts              # PageBridge interface + ChromePageBridge (chrome.scripting)
    agent/babysteps-extension.ts# pi-durable extension: prompt section + 3 tools
    agent/open-agent.ts         # builds models, registry, Harness, root conversation
    panel/panel.html, panel.ts, render.ts, settings.ts, panel.css
    background.ts               # action click → per-tab side panel
  test-pages/anmeldung.html     # static fake "Anmeldung einer Wohnung" form
  tests/                        # *.test.ts (node), *.browser.test.ts (browser mode)
```

---

### Task 1: Project scaffold + SQLite-WASM worker database

**Files:**
- Create: `package.json`, `tsconfig.json`, `vitest.config.ts`, `vitest.browser.config.ts`, `.gitignore`
- Create: `src/db/protocol.ts`, `src/db/sqlite-worker.ts`, `src/db/worker-database.ts`
- Test: `tests/worker-database.browser.test.ts`

**Interfaces:**
- Produces:
  - `class WorkerSqliteDatabase implements SqliteDatabase` (from `@earendil-works/pi-durable/storage/sqlite`)
  - `static async open(poolName: string, options?: { worker?: Worker }): Promise<WorkerSqliteDatabase>`: spawns `new Worker(new URL("./sqlite-worker.ts", import.meta.url), { type: "module" })` unless given one, installs `opfs-sahpool` with `{ name: poolName }`, opens `/pi.sqlite3`.
  - `class PoolBusyError extends Error`: thrown by `open` when the pool's access handles are held by another document.
  - `static async deletePool(poolName: string): Promise<void>` (tests only).
- RPC: each request `{ id: number, op: "exec"|"run"|"get"|"all"|"begin"|"commit"|"rollback"|"close", sql?: string, params?: SqliteValue[] }` → `{ id, ok: true, value } | { id, ok: false, error: { name, message } }`.

- [ ] **Step 1: Scaffold.** `npm init`, then install exact deps: `@earendil-works/pi-durable@1.3.0 @earendil-works/pi-ai@1.3.0 @earendil-works/chord@1.3.0 @sqlite.org/sqlite-wasm`; dev: `typescript vite vitest @vitest/browser playwright @types/chrome`. Scripts: `build` (vite build), `test` (vitest run --config vitest.config.ts), `test:browser` (vitest run --config vitest.browser.config.ts), `typecheck` (tsc --noEmit). Browser config: Playwright provider, chromium, `launch: { executablePath: "../chrome/chrome", args: ["--no-sandbox"] }`, include `tests/**/*.browser.test.ts`; set `optimizeDeps.exclude: ["@sqlite.org/sqlite-wasm"]` (it ships its own wasm loading).

- [ ] **Step 2: Write the failing tests** in `tests/worker-database.browser.test.ts`:

```ts
import { describe, expect, it } from "vitest";
import { registerStorageConformance } from "@earendil-works/pi-durable/testing";
import { SqliteStorage } from "@earendil-works/pi-durable/storage/sqlite";
import { WorkerSqliteDatabase, PoolBusyError } from "../src/db/worker-database";

let n = 0;
registerStorageConformance({ describe, expect, it }, "WorkerSqliteDatabase", async (use) => {
  const pool = `conf-${Date.now()}-${n++}`;
  const db = await WorkerSqliteDatabase.open(pool);
  try { await use(await SqliteStorage.open(db)); } finally { await db.close(); await WorkerSqliteDatabase.deletePool(pool); }
});

describe("WorkerSqliteDatabase", () => {
  it("rolls back when the transaction callback rejects", async () => {
    const db = await WorkerSqliteDatabase.open("rb");
    await db.exec("CREATE TABLE IF NOT EXISTS t (v TEXT); DELETE FROM t");
    await expect(db.transaction(async (tx) => { await tx.run("INSERT INTO t VALUES (?)", "x"); throw new Error("boom"); }))
      .rejects.toThrow("boom");
    expect(await db.all("SELECT * FROM t")).toEqual([]);
    await db.close(); await WorkerSqliteDatabase.deletePool("rb");
  });
  it("queues outside calls until the open transaction settles", async () => {
    const db = await WorkerSqliteDatabase.open("q");
    await db.exec("CREATE TABLE IF NOT EXISTS t (v TEXT); DELETE FROM t");
    const order: string[] = [];
    const tx = db.transaction(async (t) => { await t.run("INSERT INTO t VALUES ('a')"); await new Promise(r => setTimeout(r, 30)); order.push("tx"); });
    const outside = db.run("INSERT INTO t VALUES ('b')").then(() => order.push("outside"));
    await Promise.all([tx, outside]);
    expect(order).toEqual(["tx", "outside"]);
    await db.close(); await WorkerSqliteDatabase.deletePool("q");
  });
  it("persists across close and reopen", async () => { /* write a row, close, reopen same pool, row is there */ });
  it("second open of the same pool fails with PoolBusyError", async () => {
    const a = await WorkerSqliteDatabase.open("busy");
    await expect(WorkerSqliteDatabase.open("busy")).rejects.toBeInstanceOf(PoolBusyError);
    await a.close(); await WorkerSqliteDatabase.deletePool("busy");
  });
});
```

- [ ] **Step 3: Run** `npm run test:browser`. Expected: FAIL, module `../src/db/worker-database` not found.

- [ ] **Step 4: Implement** `protocol.ts`, `sqlite-worker.ts`, `worker-database.ts`. Worker: `sqlite3InitModule()` → `installOpfsSAHPoolVfs({ name: poolName })` → `new pool.OpfsSAHPoolDb("/pi.sqlite3")`; `exec` uses `db.exec(sql)`; `run/get/all` use a prepared-statement cache keyed by SQL text, `bind(params)`, `get({})` rows as objects; `bigint` passes through. Map the sahpool "access handle busy/NoModificationAllowedError" failure to an error named `PoolBusyError`. Client: one in-flight transaction at a time. `transaction(cb)` sends `begin` (`BEGIN IMMEDIATE`), gives `cb` an executor bound to the transaction, then `commit`, or `rollback` and rethrow the same error (`AggregateError` if rollback fails). All non-transaction calls await a client-side queue promise, so they wait for the open transaction, as the `SqliteDatabase` contract requires. `close` closes the db, pauses the VFS, and terminates the worker.

- [ ] **Step 5: Run** `npm run test:browser`. Expected: conformance suite and the 4 named tests PASS. Also `npm run typecheck` passes.

- [ ] **Step 6: Commit** `feat(durable): SQLite-WASM OPFS worker database for pi-durable`.

---

### Task 2: Per-tab database key

**Files:**
- Create: `src/tab-key.ts`
- Test: `tests/tab-key.test.ts`

**Interfaces:**
- Produces:
  - `interface SessionArea { get(key: string): Promise<Record<string, unknown>>; set(items: Record<string, unknown>): Promise<void> }` (matches `chrome.storage.session`)
  - `async function getBrowserSessionId(area: SessionArea = chrome.storage.session): Promise<string>`
  - `function databaseKey(sessionId: string, tabId: number): string`: returns `` `${sessionId}-${tabId}` ``, a valid sahpool name (only `[A-Za-z0-9-]`).

- [ ] **Step 1: Failing tests:**
  - `creates and reuses one session id`: two calls on the same fake area return the same UUID; the area holds `browserSessionId`.
  - `different sessions give different keys for the same tab`: `databaseKey("a", 7) !== databaseKey("b", 7)`; `databaseKey("s", 7) === "s-7"`.
  - `concurrent first calls agree`: `Promise.all([get(area), get(area)])` yields equal ids (serialize through a module-level promise).
- [ ] **Step 2: Run** `npm test -- tab-key`. Expected: FAIL (module missing).
- [ ] **Step 3: Implement** with `crypto.randomUUID()`.
- [ ] **Step 4: Run** `npm test -- tab-key`. Expected: PASS.
- [ ] **Step 5: Commit** `feat(durable): per-tab database key`.

---

### Task 3: Page script (snapshot, glow, clear) + test page

**Files:**
- Create: `src/page/page-script.ts`, `test-pages/anmeldung.html`
- Test: `tests/page-script.browser.test.ts`

**Interfaces:**
- Produces (installed idempotently on `window.__babysteps` when the bundle runs; also exported for tests):
  - `snapshot(options?: { maxChars?: number }): { text: string; truncated: boolean; url: string; title: string }`. Default `maxChars` is 12000. One line per visible element in DOM order, format `[<id>] <role> "<name>"` plus `value="…"`/`checked`/`required` where relevant, headings as `## <text>`. Ids are `b1`, `b2`, …, stamped as `data-babysteps-id`. Re-snapshot reuses an element's existing id. Elements included: `a[href]`, `button`, `input:not([type=hidden])`, `select`, `textarea`, `[role=button|link|checkbox|radio|tab|menuitem|switch]`, `h1–h3`, and `label` text attached to inputs as their names. Skip invisible elements (`display:none`, `visibility:hidden`, zero size, `aria-hidden=true`).
  - `highlight(id: string, label?: string): { ok: true } | { ok: false; reason: "not_found" }`: one overlay at a time (a new highlight replaces the old one), scrolls the element into view (`block: "center"`, smooth), and adds a pulsing glow. Use a fixed-position overlay element `#babysteps-glow` that tracks the target's `getBoundingClientRect()` on scroll/resize, not a style on the target, so page CSS can't hide it. Show the optional `label` in a large, high-contrast bubble beside it. All overlay DOM sits in a shadow root on `#babysteps-root`.
  - `clearHighlights(): void`.
- `test-pages/anmeldung.html`: a German "Anmeldung einer Wohnung" form with fields for Familienname, Vornamen, Geburtsdatum, neue Anschrift (Straße, Hausnummer, PLZ, Ort), Einzugsdatum, a "Wohnungsgeberbestätigung hochladen" file input, a hidden input, a collapsed `display:none` section, and a "Weiter" button. No external resources.

- [ ] **Step 1: Failing tests** (load fixture HTML into `document.body`):
  - `snapshot lists visible fields with labels`: text contains `textbox "Familienname"` and `button "Weiter"`, and does not contain the hidden or `display:none` fields.
  - `snapshot ids are stable across calls`: the id for "Familienname" is the same in two snapshots.
  - `snapshot truncates to maxChars and says so`: with `maxChars: 200`, `text.length <= 260` and `truncated === true`, and the text ends with a line saying the list was cut.
  - `highlight shows one glow over the element`: after `highlight(id, "Hier Ihren Nachnamen")`, the shadow root has one glow element whose rect overlaps the target and whose label text matches. A second highlight leaves exactly one glow.
  - `highlight returns not_found for a removed id`: remove the element, then expect `{ ok: false, reason: "not_found" }`.
  - `clearHighlights removes the overlay`.
- [ ] **Step 2: Run** `npm run test:browser -- page-script`. Expected: FAIL.
- [ ] **Step 3: Implement.** Accessible name order: `aria-label`, `aria-labelledby` text, `<label for>` or wrapping label, `placeholder`, `title`, then trimmed text content (collapsed whitespace, cut at 80 chars).
- [ ] **Step 4: Run** the same command. Expected: PASS.
- [ ] **Step 5: Commit** `feat(durable): page snapshot and glow overlay`.

---

### Task 4: BabySteps pi-durable extension + agent opener

**Files:**
- Create: `src/page/bridge.ts`, `src/agent/babysteps-extension.ts`, `src/agent/open-agent.ts`
- Test: `tests/agent.test.ts` (Node; `MemoryStorage` + pi-ai `fauxProvider`)

**Interfaces:**
- Consumes: `snapshot`/`highlight`/`clearHighlights` result shapes from Task 3.
- Produces:
  - `interface PageBridge { snapshot(): Promise<SnapshotResult>; highlight(id: string, label?: string): Promise<HighlightResult>; clear(): Promise<void> }`. Every method rejects with `PageUnavailableError` when injection is impossible.
  - `class ChromePageBridge implements PageBridge { constructor(tabId: number) }`: each call first runs `chrome.scripting.executeScript({ target: { tabId }, files: ["page-script.js"] })`, which is idempotent, then `executeScript({ target: { tabId }, func: (…) => window.__babysteps.<fn>(…), args })`. Maps executeScript failures to `PageUnavailableError`.
  - `function createBabyStepsExtension(bridge: PageBridge): Extension`: name `"babysteps"`; one `section("babysteps", …, { tag: false })` holding the system prompt; tools `read_page` (no params), `highlight` (`{ id: string, label?: string }`, label ≤ 60 chars), `clear_highlights` (no params), all `replay: "safe"`.
  - `interface OpenAgentOptions { storage: Storage; apiKey: string; bridge: PageBridge; models?: MutableModels }`. `models` lets tests pass a faux provider; production builds `createModels({ credentials, authContext: { env: async () => undefined, fileExists: async () => false } })` with `anthropicProvider()` and an `InMemoryCredentialStore` pre-filled via `modify("anthropic", async () => ({ type: "api_key", key: apiKey }))`.
  - `async function openAgent(opts: OpenAgentOptions, context: Context): Promise<{ harness: Harness; root: Conversation }>`: `Harness.open(storage, { models, registry }, context)`, then `harness.root(context, { agent: { model: { provider: "anthropic", modelId: "claude-sonnet-5-5" }, thinkingLevel: "off" } })`. Does **not** call `resume()`; the panel decides when.
- System prompt content (exact intent; the wording is the builder's): the user may be elderly and unsure with computers. Use simple German or the user's language, short sentences, one step at a time. Always `read_page` before pointing. Point with `highlight` and a short label instead of describing positions. Never claim to click or type. You cannot act on the page. Re-read the page after the user says they did something. If the page can't be read, say so plainly and suggest what to open.

- [ ] **Step 1: Failing tests** using a `FakeBridge`:
  - `read_page returns the snapshot text to the model`: faux responses `[fauxAssistantMessage(fauxToolCall("read_page", {})), fauxAssistantMessage("Bitte tragen Sie Ihren Namen ein.")]`. After `submit` + `wait`, the transcript has a `pi.tool-result` whose output contains the fake snapshot text, and the submission is `done`.
  - `highlight tool reports stale id as error result`: the bridge returns `{ ok: false, reason: "not_found" }`. The tool result is an error whose text mentions calling `read_page` again, and the run still finishes.
  - `read_page tool turns injection failure into error result`: the bridge rejects with `PageUnavailableError`. The error result text says the page can't be read; no throw escapes `wait`.
  - `api key never appears in storage`: after a run with key `"sk-test-SECRET"`, serialize all transcript entries and docs (`root.viewState` value) and assert the string is absent.
- [ ] **Step 2: Run** `npm test -- agent`. Expected: FAIL.
- [ ] **Step 3: Implement** the three files.
- [ ] **Step 4: Run** `npm test -- agent`. Expected: PASS. Also run `npm run typecheck`.
- [ ] **Step 5: Commit** `feat(durable): babysteps pi-durable extension and agent opener`.

---

### Task 5: Side panel, background, manifest, build

**Files:**
- Create: `manifest.json` (in `public/` so Vite copies it), `src/background.ts`, `src/panel/panel.html`, `src/panel/panel.ts`, `src/panel/render.ts`, `src/panel/settings.ts`, `src/panel/panel.css`, `vite.config.ts`, `scripts/chrome.sh`
- Test: `tests/render.test.ts` (Node, jsdom), `tests/settings.test.ts`, `tests/panel-durability.browser.test.ts`

**Interfaces:**
- Consumes: `WorkerSqliteDatabase.open`, `PoolBusyError` (Task 1); `getBrowserSessionId`, `databaseKey` (Task 2); `ChromePageBridge`, `openAgent` (Task 4).
- Produces:
  - `function renderView(view: ConversationView, root: HTMLElement): void` (`render.ts`): user bubbles, assistant text, the streamed partial from `docs["pi.live"]`, a one-line tool chip ("Looked at the page", "Highlighted: <label>", "Cleared highlights"), and an `unanswered` reason as plain text. Pure DOM; no chrome APIs.
  - `async function loadApiKey(area = chrome.storage.local): Promise<string | undefined>`, `async function saveApiKey(key: string, area = chrome.storage.local): Promise<void>` (`settings.ts`).
- `background.ts`: on `chrome.action.onClicked`, call `await chrome.sidePanel.setOptions({ tabId: tab.id, path: \`panel.html?tab=${tab.id}\`, enabled: true })` and `chrome.sidePanel.open({ tabId: tab.id })`. The `open` call must happen in the same user-gesture tick, so start `setOptions` without awaiting it before `open`, or follow Chrome's documented pattern. On `chrome.tabs.onRemoved`, do nothing (old databases are kept per spec).
- `panel.ts` flow: read `tab` from the query string → `getBrowserSessionId()` → `databaseKey` → `WorkerSqliteDatabase.open(key)`. On `PoolBusyError`, retry 5× at 200 ms, then show "This tab's helper is open elsewhere". Then `SqliteStorage.open(db)` → load key (if missing, show the key form and stop) → `openAgent(...)` → `root.viewState(ctx).subscribe(v => renderView(v, el))` → `harness.resume()`. Send: `root.submit({ type: "input", content, requestId: crypto.randomUUID() }, ctx)`. "New task" button: `root.reset(undefined, ctx)` plus `bridge.clear()`. On `pagehide`: `harness.close(ctx)` (best effort).
- `vite.config.ts`: inputs `src/panel/panel.html`, `src/background.ts`, `src/page/page-script.ts` (IIFE, output `page-script.js` at dist root), worker as a module worker. Output `dist/` with `panel.html`, `background.js`, and `page-script.js` at the root, matching the manifest paths.
- `scripts/chrome.sh`: `exec ../chrome/chrome --user-data-dir="$DIR/.chrome-profile" --no-first-run --no-default-browser-check --load-extension="$DIR/dist" "$@"` (resolve `DIR` as the `durable/` path, like the root script).

- [ ] **Step 1: Failing tests:**
  - `render.test.ts › renders user, assistant and tool chip`: a hand-built view with a user entry, an assistant tool call to `highlight` with label "Nachname", a tool result, and a final text gives three bubbles plus a chip reading `Highlighted: Nachname`.
  - `render.test.ts › shows unanswered reason as text`.
  - `settings.test.ts › missing key blocks submit with message`: `loadApiKey` on an empty fake area returns `undefined`. Export `canSubmit(key: string | undefined): { ok: boolean; message?: string }` from `settings.ts`, returning `{ ok: false, message: "Bitte zuerst den API-Schlüssel eintragen." }`.
  - `panel-durability.browser.test.ts › transcript survives close and reopen`: open a `WorkerSqliteDatabase` pool → `openAgent` with a faux provider → submit and wait → close the harness and db → reopen the same pool → `root.viewState` has the same user and assistant entries.
  - `panel-durability.browser.test.ts › interrupted run resumes after reopen`: faux provider with a slow first response (`tokensPerSecond` low). Submit, close the harness and db mid-stream, reopen, `resume()`, `wait` the same submission via `harness.submission(id)`. It ends `done`.
- [ ] **Step 2: Run** `npm test && npm run test:browser`. Expected: the new tests FAIL.
- [ ] **Step 3: Implement** all files listed above.
- [ ] **Step 4: Run** `npm test && npm run test:browser && npm run typecheck && npm run build`. Expected: all PASS; `dist/` contains `manifest.json`, `panel.html`, `background.js`, `page-script.js`, the worker chunk, and `sqlite3.wasm`.
- [ ] **Step 5: Commit** `feat(durable): per-tab side panel running the durable agent`.

---

### Task 6: End-to-end manual verification + README

**Files:**
- Create: `README.md` (how to build, launch, load the key, and the known limits from the spec's "Open risks")

- [ ] **Step 1: Build and launch.** `npm run build && scripts/chrome.sh --no-sandbox file://$PWD/test-pages/anmeldung.html`. In `chrome://extensions`, enable "Allow access to file URLs" for the extension (file pages need it). Expected: the extension icon shows; clicking it opens the side panel for that tab.
- [ ] **Step 2: Key.** Paste the Anthropic key and send "Ich möchte mich anmelden, was muss ich tun?". Expected: a "Looked at the page" chip, a short plain answer, and the Familienname field glowing with a label.
- [ ] **Step 3: Durability.** Send a second message and close the side panel while the answer streams. Reopen it via the icon. Expected: the full transcript is visible and the run finishes or ends cleanly with no duplicate user message.
- [ ] **Step 4: Per-tab isolation.** Open a second tab (e.g. `https://www.google.com`), open its panel, and ask something different. Switch back to tab 1. Expected: tab 1's transcript is unchanged. In DevTools → Application → Storage, OPFS has two pool directories named `<session>-<tabId>`.
- [ ] **Step 5: Edge pages.** Open `chrome://settings` and its panel, then ask for help. Expected: the agent says it can't see this page; nothing crashes. Remove the key in settings, reload the panel, and try to send. Expected: the German "API-Schlüssel" message.
- [ ] **Step 6: Network.** Open the panel's DevTools Network tab. Expected: requests only to `api.anthropic.com`.
- [ ] **Step 7: Record** which open risks were confirmed (panel document lifecycle on tab switch; sahpool reacquire on reopen) in `README.md`, then commit `docs(durable): README and verification notes`.
