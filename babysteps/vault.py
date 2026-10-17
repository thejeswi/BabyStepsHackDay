"""The password book: a deliberately simple password manager for the demo.

The agent only ever sees entry names, sites and usernames. Passwords go from this file
straight into the browser field (browser.fill_secret) and never into a tool result, a
model message or the session log.

NOT secure storage: passwords sit in plain JSON on disk (config.VAULT_FILE, git-ignored).
Fine for a demo; a real product would use the OS keychain or an encrypted vault.
"""
import json
import secrets
import string
from urllib.parse import urlparse

from . import config
from .browser import ToolError

_ALPHABET = string.ascii_letters + string.digits + "-_!?"


def _load() -> list[dict]:
    if not config.VAULT_FILE.exists():
        return []
    return json.loads(config.VAULT_FILE.read_text())


def _save(entries: list[dict]) -> None:
    config.VAULT_FILE.write_text(json.dumps(entries, indent=2))


def site_of(url: str) -> str:
    return (urlparse(url).hostname or "").lower()


def listing() -> str:
    """What the agent may see: no passwords."""
    entries = _load()
    if not entries:
        return "The password book is empty."
    return "Password book entries (passwords hidden):\n" + "\n".join(
        f"- {e['name']} | site: {e['site']} | username: {e['username']}" for e in entries
    )


def get(name: str) -> dict:
    for e in _load():
        if e["name"] == name:
            return e
    raise ToolError(f"No entry called {name!r}. Call list_passwords to see the exact names.")


def check_site(entry: dict, page_url: str) -> None:
    """Refuse to fill a password on a different site than it was saved for (phishing guard)."""
    host = site_of(page_url)
    site = entry["site"]
    if not (host == site or host.endswith("." + site)):
        raise ToolError(
            f"Refused: the entry {entry['name']!r} belongs to {site}, but this page is {host or page_url}. "
            "Passwords are only filled on their own site. If this page claims to be that site, it may be fake."
        )


def put(name: str, site: str, username: str, password: str) -> None:
    if not password:
        raise ToolError("Refused to save an empty password")
    entries = [e for e in _load() if e["name"] != name]
    entries.append({"name": name, "site": site.lower(), "username": username, "password": password})
    _save(entries)


def generate() -> str:
    return "".join(secrets.choice(_ALPHABET) for _ in range(16))


def entries_for_human() -> list[dict]:
    return _load()
