"""Settings, paths and environment loading. Everything configurable lives here."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = ROOT / "static"
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)
# What the helper remembers about its user, as readable Markdown files (memory tool backend).
# resolve(): on macOS /var is a symlink to /private/var; unresolved paths break relative_to().
MEMORY_DIR = Path(os.environ.get("BABYSTEPS_MEMORY_DIR", ROOT / "memory")).resolve()
MEMORY_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv(ROOT / ".env")

PORT = int(os.environ.get("BABYSTEPS_PORT", "8000"))
BASE_URL = f"http://127.0.0.1:{PORT}"

MODEL = os.environ.get("BABYSTEPS_MODEL", "claude-opus-5-5")
# Opus 5.5 defaults to "medium"; set explicitly so a model swap doesn't silently change it.
EFFORT = os.environ.get("BABYSTEPS_EFFORT", "medium")
# Server-side refusal fallback (beta). Set BABYSTEPS_FALLBACKS=0 if the API rejects it.
USE_FALLBACKS = os.environ.get("BABYSTEPS_FALLBACKS", "1") == "1"

# Hosts the agent's browser may navigate to. Navigations anywhere else are blocked
# by the browser itself, not by the prompt. Comma-separated; subdomains are included.
ALLOWED_HOSTS = [
    h.strip().lower()
    for h in os.environ.get(
        "BABYSTEPS_ALLOWED_HOSTS", "127.0.0.1,localhost,bvg.de,wikipedia.org"
    ).split(",")
    if h.strip()
]
# Paths the agent must never open even on allowed hosts. The fake phone stands in for
# the user's real phone: the agent must not read the user's codes.
BLOCKED_PATH_PREFIXES = ["/mock/phone"]

# Where the agent's browser window sits: the right half of a typical laptop screen.
BROWSER_WINDOW_POSITION = os.environ.get("BABYSTEPS_WINDOW_POS", "760,0")
BROWSER_WINDOW_SIZE = os.environ.get("BABYSTEPS_WINDOW_SIZE", "760,900")

# Headless only for automated tests; the demo needs the visible window.
HEADLESS = os.environ.get("BABYSTEPS_HEADLESS", "0") == "1"

MAX_STEPS_PER_TURN = 30
PAGE_TEXT_LIMIT = 6000  # characters of visible page text sent to the model per read
MAX_ELEMENTS = 150      # interactive elements listed per read


def require_api_key() -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit(
            "ANTHROPIC_API_KEY is not set. Copy .env.example to .env and put your key in it."
        )
