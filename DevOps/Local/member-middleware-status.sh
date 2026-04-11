#!/usr/bin/env bash
# Status of the member-portal middleware microservices.

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
PID_FILE="$REPO/.run/member_middleware.pids"

SERVICES="api_gateway auth_svc member_svc appointment_svc visit_management_svc"
PORT=8001

if [ ! -f "$PID_FILE" ]; then
  echo "Member middleware: not started (no PID file)"
  exit 0
fi

PIDS=($(cat "$PID_FILE"))
IDX=0

echo "Member middleware status:"
for svc in $SERVICES; do
  pid="${PIDS[$IDX]:-?}"
  if [ "$pid" != "?" ] && kill -0 "$pid" 2>/dev/null; then
    STATUS="running"
  else
    STATUS="not running"
  fi
  printf "  %-28s :%-5s  PID %-8s %s\n" "$svc" "$PORT" "$pid" "$STATUS"
  PORT=$((PORT + 1))
  IDX=$((IDX + 1))
done
