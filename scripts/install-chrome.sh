#!/usr/bin/env bash
# Download a standalone Chrome (Chrome for Testing) into ./chrome inside this repo.
# Works on macOS (Apple Silicon + Intel) and Linux x64. Needs only curl + unzip.
# Usage: scripts/install-chrome.sh [channel]   channel: STABLE (default) | BETA | DEV | CANARY
set -euo pipefail

CHANNEL="$(echo "${1:-STABLE}" | tr '[:lower:]' '[:upper:]')"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$ROOT/chrome"
BASE="https://googlechromelabs.github.io/chrome-for-testing"

case "$(uname -s)-$(uname -m)" in
  Darwin-arm64)  PLATFORM=mac-arm64 ;;
  Darwin-x86_64) PLATFORM=mac-x64 ;;
  Linux-x86_64)  PLATFORM=linux64 ;;
  *) echo "Unsupported platform: $(uname -s)-$(uname -m)" >&2; exit 1 ;;
esac

VERSION="$(curl -fsSL "$BASE/LATEST_RELEASE_$CHANNEL")"
URL="https://storage.googleapis.com/chrome-for-testing-public/$VERSION/$PLATFORM/chrome-$PLATFORM.zip"

if [[ -f "$DEST/VERSION" && "$(cat "$DEST/VERSION")" == "$VERSION" ]]; then
  echo "Chrome $VERSION already installed in $DEST"
  exit 0
fi

echo "Downloading Chrome $CHANNEL $VERSION ($PLATFORM)..."
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
curl -fL --progress-bar "$URL" -o "$TMP/chrome.zip"
unzip -q "$TMP/chrome.zip" -d "$TMP"

rm -rf "$DEST"
mv "$TMP/chrome-$PLATFORM" "$DEST"
echo "$VERSION" > "$DEST/VERSION"

if [[ "$PLATFORM" == mac-* ]]; then
  # Clear Gatekeeper quarantine in case the zip was fetched via a browser or AirDrop.
  xattr -cr "$DEST/Google Chrome for Testing.app" 2>/dev/null || true
fi

"$ROOT/scripts/chrome.sh" --version
