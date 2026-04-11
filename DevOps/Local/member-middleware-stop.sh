#!/usr/bin/env bash
# Stop the member-portal middleware microservices.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
PID_FILE="$REPO/.run/member_middleware.pids"

if [ ! -f "$PID_FILE" ]; then
  echo "No PID file found — member middleware not running."
  exit 0
fi

for pid in $(cat "$PID_FILE"); do
  if kill -0 "$pid" 2>/dev/null; then
    kill "$pid" 2>/dev/null && echo "Stopped PID $pid" || echo "Could not stop PID $pid"
  else
    echo "PID $pid: already stopped"
  fi
done

rm -f "$PID_FILE"
echo "Member middleware stopped."
