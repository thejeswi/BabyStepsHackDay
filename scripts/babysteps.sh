#!/usr/bin/env bash
# Start BabySteps: the repo's Chrome with the chat side panel extension, plus the agent
# server attached to that Chrome. Stopping this script (Ctrl+C) closes Chrome too.
# Works on macOS and Linux. One-time setup: see README ("Run it").
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CDP_PORT="${BABYSTEPS_CDP_PORT:-9222}"
PROFILE="$ROOT/.chrome-profile"
cd "$ROOT"

if [[ ! -x .venv/bin/python ]]; then
  echo "Python environment missing. Run: python3 -m venv .venv && .venv/bin/pip install -e ." >&2
  exit 1
fi
.venv/bin/python -c "from babysteps import config; config.require_api_key()"

[[ -f chrome/VERSION ]] || scripts/install-chrome.sh

# A Chrome already running on this profile would swallow our flags and open a plain window.
if [[ -L "$PROFILE/SingletonLock" ]]; then
  pid="$(readlink "$PROFILE/SingletonLock" | sed 's/.*-//')"
  if kill -0 "$pid" 2>/dev/null; then
    echo "The BabySteps Chrome is already open. Close it first, then run this again." >&2
    exit 1
  fi
fi

FLAGS=(--remote-debugging-port="$CDP_PORT" --load-extension="$ROOT/extension")
# Ubuntu 23.10+ blocks Chrome's sandbox for browsers outside /opt (AppArmor userns restriction).
if [[ "$(cat /proc/sys/kernel/apparmor_restrict_unprivileged_userns 2>/dev/null)" == 1 ]]; then
  echo "Note: this Linux blocks Chrome's sandbox; starting with --no-sandbox (OK for a demo)." >&2
  FLAGS+=(--no-sandbox)
fi

# Start on a blank tab; the agent takes it over (one tab instead of two).
scripts/chrome.sh "${FLAGS[@]}" about:blank >"$ROOT/logs/chrome.log" 2>&1 &
CHROME_PID=$!
trap 'kill "$CHROME_PID" 2>/dev/null || true' EXIT

for _ in $(seq 1 60); do
  curl -fs "http://127.0.0.1:$CDP_PORT/json/version" >/dev/null && break
  kill -0 "$CHROME_PID" 2>/dev/null || { echo "Chrome exited; see logs/chrome.log" >&2; exit 1; }
  sleep 0.5
done

echo "Chrome is ready. Click the BabySteps button in the toolbar (puzzle icon → BabySteps) to open the chat."
BABYSTEPS_CDP_URL="http://127.0.0.1:$CDP_PORT" .venv/bin/python -m babysteps
