#!/usr/bin/env bash
#
# Thorough teardown of the local stack.
#
#   1. Stop processes recorded in /tmp/ihcp_*.pids
#   2. Sweep the canonical port set (8001-8009 middleware, 3001-3003 portals)
#      and kill anything still listening — catches processes started outside
#      `npm run local:start-all`, e.g. an `npx vite` you ran by hand or a
#      portal you launched in another terminal.
#   3. Bring down the docker compose stacks.
#
# Safe to run when nothing is up: every step is a no-op if there's nothing
# to do.
set -uo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"

echo "=== Stopping recorded middleware/portal PIDs ==="
for pid_file in /tmp/ihcp_middleware.pids /tmp/ihcp_portals.pids "$REPO/.run/member_middleware.pids"; do
  if [ -f "$pid_file" ]; then
    for pid in $(cat "$pid_file"); do
      if kill -0 "$pid" 2>/dev/null; then
        kill "$pid" 2>/dev/null && echo "  killed PID $pid (from $(basename "$pid_file"))"
      fi
    done
    rm -f "$pid_file"
  fi
done

echo ""
echo "=== Sweeping canonical port set ==="
PORTS="8001 8002 8003 8004 8005 8006 8007 8008 8009 3001 3002 3003"
for port in $PORTS; do
  pids="$(lsof -nP -iTCP:"$port" -sTCP:LISTEN -t 2>/dev/null || true)"
  if [ -n "$pids" ]; then
    for pid in $pids; do
      cmd="$(ps -p "$pid" -o comm= 2>/dev/null || echo unknown)"
      echo "  killing PID $pid ($cmd) listening on :$port"
      kill "$pid" 2>/dev/null || true
    done
  fi
done

# Some children (vite via npm exec, electron renderer) need a moment to
# notice their parent is gone. Give them a beat, then SIGKILL the stragglers.
sleep 1
for port in $PORTS; do
  pids="$(lsof -nP -iTCP:"$port" -sTCP:LISTEN -t 2>/dev/null || true)"
  if [ -n "$pids" ]; then
    for pid in $pids; do
      echo "  SIGKILL straggler PID $pid on :$port"
      kill -9 "$pid" 2>/dev/null || true
    done
  fi
done

echo ""
echo "=== Bringing docker stacks down ==="
bash "$REPO/DevOps/Local/docker-all-down.sh"

echo ""
echo "Local stack fully shut down."
