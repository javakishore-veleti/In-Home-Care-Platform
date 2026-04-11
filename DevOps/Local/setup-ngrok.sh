#!/usr/bin/env bash
#
# One-time ngrok install + auth check.
#
#   1. brew-installs ngrok if it isn't on PATH
#   2. Checks for an authtoken in the standard ngrok config locations
#   3. If neither check passes, prints the exact signup + authtoken
#      install command the user has to run by hand (one-time, per
#      laptop). ngrok refuses to start without an authtoken since
#      ngrok 3.x — there is no API to bypass this.
#
# Called by `npm run setup:local:ngrok`.
set -uo pipefail

ok() { printf '  \033[32m✓\033[0m %s\n' "$*"; }
warn() { printf '  \033[33m!\033[0m %s\n' "$*"; }
err() { printf '  \033[31m✗\033[0m %s\n' "$*"; }

echo "=== ngrok install ==="
if command -v ngrok >/dev/null 2>&1; then
  ok "ngrok already installed at $(command -v ngrok) ($(ngrok --version 2>/dev/null | head -1))"
else
  if ! command -v brew >/dev/null 2>&1; then
    err "ngrok is not installed and Homebrew is not available."
    echo "  Install ngrok from https://ngrok.com/download and rerun this script."
    exit 1
  fi
  echo "  installing ngrok via Homebrew (this may take a minute)..."
  if brew install ngrok/ngrok/ngrok; then
    ok "ngrok installed at $(command -v ngrok)"
  else
    err "brew install failed — see output above."
    exit 1
  fi
fi

echo ""
echo "=== ngrok authtoken check ==="
# ngrok 3 stores its config under ~/Library/Application Support/ngrok/
# on macOS and ~/.config/ngrok/ on Linux. The file always contains an
# `authtoken:` line if a token has been installed.
CONFIG_PATHS=(
  "$HOME/Library/Application Support/ngrok/ngrok.yml"
  "$HOME/.config/ngrok/ngrok.yml"
  "$HOME/.ngrok2/ngrok.yml"
)
HAS_TOKEN=false
for path in "${CONFIG_PATHS[@]}"; do
  if [ -f "$path" ] && grep -q '^authtoken:' "$path" 2>/dev/null; then
    ok "authtoken found at $path"
    HAS_TOKEN=true
    break
  fi
done

if ! $HAS_TOKEN; then
  warn "no ngrok authtoken installed"
  echo ""
  echo "  ngrok 3.x refuses to start without a free authtoken."
  echo "  This is a one-time, per-laptop step:"
  echo ""
  echo "    1. Sign up (free):  https://dashboard.ngrok.com/signup"
  echo "    2. Copy your token: https://dashboard.ngrok.com/get-started/your-authtoken"
  echo "    3. Install it:      ngrok config add-authtoken <YOUR_TOKEN>"
  echo ""
  echo "  Then rerun: npm run setup:local:ngrok"
  exit 2
fi

echo ""
ok "ngrok is ready. You can now run: npm run local:slack:tunnel:up"
