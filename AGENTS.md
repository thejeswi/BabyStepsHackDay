# Instructions for coding agents

BabySteps is a hackathon prototype: a patient helper ("Alex") for people who are not
comfortable with computers. The chat sits in Chrome's side panel, and the helper drives a
tab in the same window. Read `README.md` for what it does and how it is built; this file is
what an agent needs on top of that.

## Setup (once per machine)

```bash
python3 -m venv .venv
.venv/bin/pip install -e .
cp env/.env.example env/.env  # the human puts ANTHROPIC_API_KEY in env/.env
scripts/install-chrome.sh     # Chrome for Testing into ./chrome (~400 MB, git-ignored)
```

- The API key is the human's to provide. Never print it, paste it into chat, or commit it
  (`env/` is git-ignored except the example). Check that it is set with
  `.venv/bin/python -c "from babysteps import config; config.require_api_key()"`.
- The Chrome extension needs no installing. `scripts/babysteps.sh` loads `extension/`
  with `--load-extension` on every start. This only works with the repo's Chrome for
  Testing; branded Google Chrome ignores the flag since version 137.
- The one thing only the human can do: open the side panel (puzzle icon → BabySteps,
  pin it once). There is no API for opening it.

## Run

```bash
scripts/babysteps.sh          # Chrome + side panel + agent server; Ctrl+C stops both
```

- Uses ports 8000 (chat and demo sites) and 9222 (Chrome debugging). If you start it in
  the background for the human, wait until `curl -fs http://127.0.0.1:8000/` succeeds.
- `static/` is served from disk: page changes go live on a side-panel reload. Python
  changes, including `babysteps/prompt.py`, need a restart. Restarting closes the human's
  Chrome and ends the conversation in progress, so ask first.
- Logs: `logs/babysteps.log` (launcher and server), `logs/session-*.jsonl` (every model
  response and tool result). When the human says "it's stuck", read the last session
  entries first: often the helper has asked a question and is waiting for an answer.
- Demo reset (`DEMO.md`): delete `memory/` and `vault.json` with the app stopped. These
  hold the human's rehearsal state, so only do it when asked.

## Test

No API key needed:

```bash
BABYSTEPS_HEADLESS=1 BABYSTEPS_PORT=8011 .venv/bin/python tests/smoke_browser.py
BABYSTEPS_PORT=8015 .venv/bin/python tests/smoke_attached.py
```

Live runs cost about $1 each; run them only when the agent loop or prompt changed (commands
in `README.md`). Always set `BABYSTEPS_PORT` so tests don't collide with a running demo
on 8000.

## Rules for changes

- The chat page (`static/index.html`) must work at two widths: the side panel (360-500px)
  and a full window. After a UI change, screenshot both (Playwright with
  `executable_path="chrome/chrome"`) and check for horizontal overflow.
- Keep the safety rules intact: the site allowlist, the download block, the
  password-field block, and the confirmation before irreversible buttons
  (`babysteps/browser.py`, `babysteps/agent.py`). The model must never see passwords
  (`babysteps/vault.py`).
- The demo sites and letters are in German on purpose; the user types in English (persona:
  Ayşe, see `DEMO.md`). Use fictional names only, no real logos.
- Several people push to this repo during the hackathon. Fetch before starting, merge
  instead of rewriting history, and don't push without the human's go-ahead.
