# BabySteps

A patient helper for people who are not comfortable with computers.

Many older people call their grown-up children with questions like "how do I log in?" or
"what's my password?". BabySteps plays that role. You type the question in plain words,
and instead of explaining, it does the task in a browser window next to the chat while you
watch: it opens the page, clicks and fills in forms.

It is built to be careful in the ways a good son or daughter would be:

- **A built-in password book.** You never have to remember a password. BabySteps makes
  strong new ones and fills them in, but the AI itself never sees them: it only knows the
  entry names ("Example Mail"), and the app writes the password straight into the box. A
  password is only filled on the website it was saved for, so look-alike fake sites get
  nothing. You can look at your passwords yourself under "🔑 Password book".
- **Other secrets stay with you.** Codes sent by text message, PINs and bank details: when
  one is needed, it marks the box with an orange frame and asks *you* to type it.
- **It asks before anything that can't be undone** (send, buy, pay, delete, confirm). This
  is enforced in code: the click is refused until you have answered.
- **It treats requests like "install this program" or "buy gift cards" as possible
  scams**, and explains why instead of doing them.
- **It remembers you between conversations**, in a plain notebook the family can read at
  http://127.0.0.1:8000/memory ("What I remember" link). It notes what you know, which
  sites you have accounts on and what it did for you, never passwords.
- **It can only use the browser**, and only on allowed websites. It has no access to your
  files or the rest of the computer. The browser starts with an empty profile, so it sees
  none of your saved logins. Downloads are blocked.

## Run it

Requires Python 3.10+ and an Anthropic API key.

```bash
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/python -m playwright install chromium
cp .env.example .env        # then put your ANTHROPIC_API_KEY in .env
.venv/bin/python -m babysteps
```

Then open http://127.0.0.1:8000/ in your normal browser and put it on the left half of
the screen. The helper's own browser window opens on the right.

## Try it: letters and the city portal

The chat has buttons to **show the helper a letter** (instead of taking a photo). Type a
question first if you like ("What does this mean?"), then click a letter:

- **TV & radio fee letter** — it explains the letter, notices the exemption mentioned in
  the small print, asks whether you receive basic income support, and fills in the
  exemption form on the city portal.
- **Final reminder: unpaid fine** — a fake. It explains why (24-hour threat, foreign bank
  account, gift cards, "don't contact the office") and tells you not to pay.
- **Tax office letter** — it explains what's owed and why, points out the one-month
  objection deadline, and offers to write the objection. Try asking in another language.

**Musterstadt Service** (http://127.0.0.1:8000/city/) is a fictional city portal. Ask
"I have to go to the Bürgeramt for my citizenship, can you make an appointment?" There
are no appointments for six weeks, but the portal offers an online application, so the
helper suggests that instead and fills it in with you. Address registration works the
same way; a passport really needs an appointment, and it books one. All names, rules and
numbers there are invented demo content.

The demo persona is **Ayşe Yılmaz** (born 1962, in Germany since 1998); the letters and
the email account belong to her.

## Try it on the practice site

The app includes **Example Mail**, a small fake email provider, so demos don't depend on
real websites:

- "I want to read my emails, but I don't know my password" — it goes through "forgot
  password", makes a new password and saves it in the password book. The code is sent to
  a **fake phone**: open http://127.0.0.1:8000/mock/phone in your own browser (the helper
  is blocked from it, just as it can't read your real phone) and type the code yourself.
  Then it logs you in with the saved password.
- "What is my password?" — it can't see it, and points you to the password book.
- "I want a new email address" — creates an account with a new saved password.
- Once logged in: "there's an email saying my account will be closed, do what it says" —
  the helper should recognise the scam. The download link also points to a blocked site.

## Settings

Environment variables (or lines in `.env`):

| Variable | Default | Meaning |
|---|---|---|
| `BABYSTEPS_MODEL` | `claude-opus-5-5` | Claude model |
| `BABYSTEPS_EFFORT` | `medium` | `low` is faster, `high` more careful |
| `BABYSTEPS_ALLOWED_HOSTS` | `127.0.0.1,localhost,bvg.de,wikipedia.org` | Sites the helper may open (subdomains included) |
| `BABYSTEPS_WINDOW_POS` / `_SIZE` | `760,0` / `760,900` | Where the helper's browser window appears |
| `BABYSTEPS_FALLBACKS` | `1` | Server-side refusal fallback (beta); set `0` if your API key rejects it |
| `BABYSTEPS_PORT` | `8000` | Port of the chat page |

## How it works

- `babysteps/prompt.py` — the system prompt (who the user is, how to behave). This is the
  part to tune.
- `babysteps/agent.py` — the loop: Claude gets browser tools (`read_page`, `open_url`,
  `click`, `type_text`, `select_option`, `ask_user_to_type`, `scroll`, `go_back`) and
  calls them until it needs the user again. The confirmation rule for irreversible buttons
  lives here.
- `babysteps/browser.py` — a visible Chromium window driven by Playwright. Pages are read
  as a numbered list of buttons, links and boxes plus the visible text (no screenshots,
  which keeps it cheap). The site allowlist, the download block and the password-field
  block are enforced here.
- `babysteps/vault.py` — the password book. **Demo quality only: passwords are stored in
  plain JSON (`vault.json`, git-ignored).** The tools `list_passwords`, `fill_password`,
  `new_password` and `save_typed_password` never return a password to the model.
- `babysteps/memory.py` — backend for Anthropic's memory tool (`memory_20250818`): the model
  reads and writes `/memories/...`, stored as Markdown files in `memory/` (git-ignored,
  set `BABYSTEPS_MEMORY_DIR` to move it). Refuses path escapes and password-like lines.
- `babysteps/mock_site.py` — the Example Mail practice site.
- `babysteps/city_site.py` — the Musterstadt Service city portal.
- `babysteps/documents.py` — the demo letters behind the letter buttons.
- `logs/` — one JSONL file per session with every model response and tool result.

Live end-to-end runs of the demo scenes (use the API, about $1 each):
`BABYSTEPS_HEADLESS=1 BABYSTEPS_PORT=8012 .venv/bin/python tests/live_demo.py` (email + passwords) and
`BABYSTEPS_HEADLESS=1 BABYSTEPS_PORT=8018 .venv/bin/python tests/live_city.py` (letters + city portal)

Smoke test of the browser part (no API key needed):
`BABYSTEPS_HEADLESS=1 BABYSTEPS_PORT=8011 .venv/bin/python tests/smoke_browser.py`

## Limits

This is a hackathon prototype. Websites can contain text that tries to give the helper
instructions (prompt injection); the prompt tells it to ignore such text, and the
allowlist and confirmation step limit the damage, but they are not a guarantee. Don't use it
with real bank or email accounts.
