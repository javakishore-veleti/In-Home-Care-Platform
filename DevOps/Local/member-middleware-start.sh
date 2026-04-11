#!/usr/bin/env bash
# Start only the middleware microservices needed for the member portal:
#   api_gateway          :8001
#   auth_svc             :8002
#   member_svc           :8003
#   appointment_svc      :8004
#   visit_management_svc :8005
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
VENV="$HOME/runtime_data/python_venvs/In-Home-Care-Platform"
RUN_DIR="$REPO/.run"
PID_FILE="$RUN_DIR/member_middleware.pids"
LOG_DIR="$RUN_DIR/logs"
mkdir -p "$LOG_DIR"

if [ ! -f "$VENV/bin/uvicorn" ]; then
  echo "ERROR: uvicorn not found in venv. Run: npm run setup:local:venv:install"
  exit 1
fi

if [ -f "$PID_FILE" ]; then
  STILL_RUNNING=false
  for pid in $(cat "$PID_FILE"); do
    if kill -0 "$pid" 2>/dev/null; then STILL_RUNNING=true; fi
  done
  if $STILL_RUNNING; then
    echo "Member middleware already running (see $PID_FILE). Stop first with:"
    echo "  npm run local:member:middleware:stop"
    exit 1
  fi
  rm -f "$PID_FILE"
fi

# Build PYTHONPATH — shared code + each service's src
PYTHONPATH="$REPO/middleware"
for svc in api_gateway auth_svc member_svc appointment_svc visit_management_svc; do
  PYTHONPATH="$PYTHONPATH:$REPO/middleware/Microservices/$svc/src"
done
export PYTHONPATH

SERVICES="api_gateway auth_svc member_svc appointment_svc visit_management_svc"
PORT=8001
PIDS=""

for svc in $SERVICES; do
  echo "Starting $svc on :$PORT"
  "$VENV/bin/uvicorn" "${svc}.main:app" \
    --host 127.0.0.1 --port "$PORT" \
    --app-dir "$REPO/middleware/Microservices/$svc/src" \
    > "$LOG_DIR/${svc}.log" 2>&1 &
  PIDS="$PIDS $!"
  PORT=$((PORT + 1))
done

echo "$PIDS" > "$PID_FILE"
echo ""
echo "Member middleware started (ports 8001–8005)."
echo "  PIDs : $PID_FILE"
echo "  Logs : $LOG_DIR/"
