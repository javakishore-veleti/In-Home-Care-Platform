#!/usr/bin/env bash
#
# slack-tunnel — manage the public HTTP tunnel that Slack uses to
# reach slack_svc on this laptop.
#
# Subcommands:
#   up      Start ngrok against http://127.0.0.1:8009, wait for the
#           public URL, persist it, and (if SLACK_APP_ID and
#           SLACK_APP_CONFIG_TOKEN are set in .env.local) push the URL
#           into the Slack app manifest so the user does not have to
#           paste it into the admin pages by hand.
#   down    Stop the tunnel process started by `up`.
#   status  Show the current public URL (or "stopped").
#
# State files (under <repo>/.run/, gitignored via .run/):
#   slack-tunnel.pid   ngrok process id
#   slack-tunnel.url   current public https URL
#   slack-tunnel.log   ngrok stdout/stderr
#
# This script does NOT install ngrok for you. If you don't have it,
# `brew install ngrok/ngrok/ngrok` (mac) or grab it from
# https://ngrok.com/download. cloudflared support is a TODO — ngrok
# is the most common dev tunnel and has a clean inspector API.
set -uo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
RUN_DIR="$REPO/.run"
PID_FILE="$RUN_DIR/slack-tunnel.pid"
URL_FILE="$RUN_DIR/slack-tunnel.url"
LOG_FILE="$RUN_DIR/slack-tunnel.log"
INSPECTOR_URL="http://127.0.0.1:4040/api/tunnels"
LOCAL_TARGET="http://127.0.0.1:8009"
WAIT_TIMEOUT=20

mkdir -p "$RUN_DIR"

# Source .env.local so SLACK_APP_ID / SLACK_APP_CONFIG_TOKEN are visible
# to the manifest update step. Use `set -a` so every assignment is
# exported, including ones that don't already say `export`.
if [ -f "$REPO/.env.local" ]; then
  set -a
  # shellcheck disable=SC1090,SC1091
  . "$REPO/.env.local"
  set +a
fi

usage() {
  echo "usage: $0 {up|down|status}"
  exit 2
}

is_running() {
  if [ ! -f "$PID_FILE" ]; then
    return 1
  fi
  local pid
  pid="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [ -z "$pid" ]; then
    return 1
  fi
  kill -0 "$pid" 2>/dev/null
}

cmd_status() {
  if is_running; then
    local url
    url="$(cat "$URL_FILE" 2>/dev/null || echo '(unknown)')"
    echo "slack-tunnel: running (pid $(cat "$PID_FILE")), public URL = $url"
    echo "  /slack/interactivity → $url/slack/interactivity"
    echo "  /slack/events        → $url/slack/events"
  else
    echo "slack-tunnel: stopped"
  fi
}

cmd_down() {
  if is_running; then
    local pid
    pid="$(cat "$PID_FILE")"
    echo "slack-tunnel: killing pid $pid"
    kill "$pid" 2>/dev/null || true
    sleep 1
    if kill -0 "$pid" 2>/dev/null; then
      kill -9 "$pid" 2>/dev/null || true
    fi
  else
    echo "slack-tunnel: nothing to stop"
  fi
  rm -f "$PID_FILE" "$URL_FILE"
}

cmd_up() {
  if is_running; then
    echo "slack-tunnel: already running, current state:"
    cmd_status
    return 0
  fi

  if ! command -v ngrok >/dev/null 2>&1; then
    echo "ERROR: ngrok is not in PATH."
    echo "  Install with: brew install ngrok/ngrok/ngrok"
    echo "  Or download from: https://ngrok.com/download"
    exit 1
  fi

  # Refuse to start a second ngrok if one is already on :4040 — its
  # inspector API is global, not per-tunnel, so we'd just confuse
  # ourselves.
  if curl -fs --max-time 1 "$INSPECTOR_URL" >/dev/null 2>&1; then
    echo "slack-tunnel: an ngrok process is already running on :4040"
    echo "  Reusing its tunnel for $LOCAL_TARGET (assuming it points there)."
  else
    echo "slack-tunnel: starting ngrok against $LOCAL_TARGET"
    ngrok http 8009 --log=stdout > "$LOG_FILE" 2>&1 &
    echo "$!" > "$PID_FILE"
  fi

  echo "slack-tunnel: waiting up to ${WAIT_TIMEOUT}s for the public URL..."
  local public_url=""
  for i in $(seq 1 "$WAIT_TIMEOUT"); do
    public_url="$(
      curl -fs --max-time 1 "$INSPECTOR_URL" 2>/dev/null \
        | python3 -c "import sys,json; tunnels=json.load(sys.stdin).get('tunnels',[]); urls=[t['public_url'] for t in tunnels if t.get('public_url','').startswith('https')]; print(urls[0] if urls else '')" 2>/dev/null \
        || true
    )"
    if [ -n "$public_url" ]; then
      break
    fi
    sleep 1
  done

  if [ -z "$public_url" ]; then
    echo "slack-tunnel: timed out waiting for ngrok to expose a public URL"
    if [ -f "$LOG_FILE" ] && grep -q "ERR_NGROK_4018\|authentication failed" "$LOG_FILE" 2>/dev/null; then
      echo ""
      echo "  ngrok refused to start because no authtoken is installed."
      echo "  ngrok 3.x requires a free authtoken — this is a one-time"
      echo "  per-laptop step you have to do by hand:"
      echo ""
      echo "    1. Sign up (free):  https://dashboard.ngrok.com/signup"
      echo "    2. Copy your token: https://dashboard.ngrok.com/get-started/your-authtoken"
      echo "    3. Install it:      ngrok config add-authtoken <YOUR_TOKEN>"
      echo ""
      echo "  Then rerun: npm run local:slack:tunnel:up"
      echo ""
      echo "  Or run: npm run setup:local:ngrok"
      echo "  to walk through both ngrok install + auth at once."
    else
      echo "  See $LOG_FILE for details."
    fi
    cmd_down
    exit 1
  fi

  echo "$public_url" > "$URL_FILE"
  echo ""
  echo "slack-tunnel: ready"
  echo "  public URL: $public_url"
  echo "  /slack/interactivity → $public_url/slack/interactivity"
  echo "  /slack/events        → $public_url/slack/events"
  echo ""

  # Optional: auto-push the URL into the Slack app manifest so the user
  # never touches the Slack admin pages.
  if [ -n "${SLACK_APP_ID:-}" ] && [ -n "${SLACK_APP_CONFIG_TOKEN:-}" ]; then
    echo "slack-tunnel: SLACK_APP_ID + SLACK_APP_CONFIG_TOKEN set — pushing manifest update..."
    if /usr/bin/env python3 "$REPO/DevOps/Local/slack-tunnel-update-manifest.py" \
        --app-id "$SLACK_APP_ID" \
        --token "$SLACK_APP_CONFIG_TOKEN" \
        --interactivity-url "$public_url/slack/interactivity" \
        --events-url "$public_url/slack/events"; then
      echo "slack-tunnel: Slack app manifest updated successfully."
    else
      echo "slack-tunnel: WARNING — manifest update failed. Paste the URLs above into:"
      echo "  https://api.slack.com/apps/$SLACK_APP_ID/interactive-messages"
      echo "  https://api.slack.com/apps/$SLACK_APP_ID/event-subscriptions"
    fi
  else
    echo "slack-tunnel: (SLACK_APP_ID + SLACK_APP_CONFIG_TOKEN not set)"
    echo "  Paste the URLs above into the Slack app admin pages:"
    echo "    Interactivity & Shortcuts → Request URL"
    echo "    Event Subscriptions       → Request URL"
    echo "  Or set SLACK_APP_ID + SLACK_APP_CONFIG_TOKEN in .env.local to"
    echo "  have this script push the URL automatically next time."
  fi
}

case "${1:-}" in
  up) cmd_up ;;
  down) cmd_down ;;
  status) cmd_status ;;
  *) usage ;;
esac
