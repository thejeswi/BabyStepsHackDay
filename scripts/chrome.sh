#!/usr/bin/env bash
# Launch the repo-local Chrome with its own profile, isolated from any system Chrome.
# Usage: scripts/chrome.sh [chrome flags...] [url]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

case "$(uname -s)" in
  Darwin) BIN="$ROOT/chrome/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing" ;;
  *)      BIN="$ROOT/chrome/chrome" ;;
esac

if [[ ! -x "$BIN" ]]; then
  echo "Chrome not installed. Run: scripts/install-chrome.sh" >&2
  exit 1
fi

# --version should not create a profile directory.
if [[ "${1:-}" == "--version" ]]; then
  exec "$BIN" --version
fi

exec "$BIN" --user-data-dir="$ROOT/.chrome-profile" --no-first-run --no-default-browser-check "$@"
