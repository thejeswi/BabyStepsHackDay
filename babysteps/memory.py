"""Backend for Anthropic's memory tool (type memory_20250818).

The model reads and writes files under a virtual /memories directory; we map that onto a
plain folder on this computer (config.MEMORY_DIR). Files are ordinary Markdown, so a family
member can open the folder (or the /memory page) and read or correct what the helper
remembers. Secrets must never be stored here; the prompt says so, and save() refuses
text that looks like a password line.
"""
import re
from pathlib import Path

from . import config
from .browser import ToolError

VIRTUAL_ROOT = "/memories"
_SECRETISH = re.compile(r"\b(password|passwort|pin|tan|code)\s*[:=]\s*\S+", re.IGNORECASE)


def _resolve(virtual_path: str) -> Path:
    if not virtual_path.startswith(VIRTUAL_ROOT):
        raise ToolError(f"Paths must start with {VIRTUAL_ROOT}, got {virtual_path!r}")
    rel = virtual_path[len(VIRTUAL_ROOT):].lstrip("/")
    real = (config.MEMORY_DIR / rel).resolve()
    if real != config.MEMORY_DIR.resolve() and config.MEMORY_DIR.resolve() not in real.parents:
        raise ToolError(f"Path {virtual_path!r} leaves the memory directory")
    return real


def _check_no_secrets(text: str) -> None:
    if _SECRETISH.search(text):
        raise ToolError("Refused: this looks like a password or code. Never store secrets in memory.")


def handle(cmd: dict) -> str:
    """Execute one memory tool command; returns the text shown to the model."""
    c = cmd["command"]
    if c == "view":
        p = _resolve(cmd["path"])
        if p.is_dir():
            files = sorted(str(f.relative_to(config.MEMORY_DIR)) for f in p.rglob("*") if f.is_file())
            return "Files in " + cmd["path"] + ":\n" + ("\n".join(files) if files else "(empty)")
        if not p.exists():
            raise ToolError(f"{cmd['path']} does not exist")
        lines = p.read_text().splitlines()
        rng = cmd.get("view_range")  # optional per the tool spec: [start, end], 1-based
        start, end = (rng[0], rng[1]) if rng else (1, len(lines))
        end = len(lines) if end == -1 else end
        return "\n".join(f"{i}\t{lines[i - 1]}" for i in range(start, min(end, len(lines)) + 1))
    if c == "create":
        _check_no_secrets(cmd["file_text"])
        p = _resolve(cmd["path"])
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(cmd["file_text"])
        return f"Saved {cmd['path']}"
    if c == "str_replace":
        _check_no_secrets(cmd["new_str"])
        p = _resolve(cmd["path"])
        text = p.read_text()
        n = text.count(cmd["old_str"])
        if n != 1:
            raise ToolError(f"old_str found {n} times in {cmd['path']}; it must match exactly once")
        p.write_text(text.replace(cmd["old_str"], cmd["new_str"]))
        return f"Updated {cmd['path']}"
    if c == "insert":
        _check_no_secrets(cmd["insert_text"])
        p = _resolve(cmd["path"])
        lines = p.read_text().splitlines(keepends=True)
        at = cmd["insert_line"]
        if not 0 <= at <= len(lines):
            raise ToolError(f"insert_line {at} out of range (file has {len(lines)} lines)")
        text = cmd["insert_text"] if cmd["insert_text"].endswith("\n") else cmd["insert_text"] + "\n"
        lines.insert(at, text)
        p.write_text("".join(lines))
        return f"Inserted into {cmd['path']}"
    if c == "delete":
        p = _resolve(cmd["path"])
        if p == config.MEMORY_DIR.resolve():
            raise ToolError("Refusing to delete the whole memory directory")
        if not p.exists():
            raise ToolError(f"{cmd['path']} does not exist")
        if p.is_dir():
            raise ToolError("Delete files one by one")
        p.unlink()
        return f"Deleted {cmd['path']}"
    if c == "rename":
        src, dst = _resolve(cmd["old_path"]), _resolve(cmd["new_path"])
        dst.parent.mkdir(parents=True, exist_ok=True)
        src.rename(dst)
        return f"Renamed {cmd['old_path']} to {cmd['new_path']}"
    raise ToolError(f"Unknown memory command {c!r}")


def dump() -> list[tuple[str, str]]:
    """All memory files as (name, content), for the human-readable /memory page."""
    return [
        (str(f.relative_to(config.MEMORY_DIR)), f.read_text())
        for f in sorted(config.MEMORY_DIR.rglob("*"))
        if f.is_file()
    ]
