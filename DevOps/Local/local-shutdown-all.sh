#!/usr/bin/env bash
#
# Thorough teardown of the local stack.
#
#   1. Stop processes recorded in /tmp/ihcp_*.pids
#   2. Sweep the canonical port set (8001-8009 middleware, 3001-3003 portals)
#      and kill anything still listening — catches processes started outside
#      `npm run local:start-all`, e.g. an `npx vite` you ran by hand or a
#      portal you launched in another terminal.
#   3. Bring down every docker compose stack with `down -v` so volumes
#      (postgres-data, kafka-data, etc.) are wiped — that is the
#      *shutdown* contract; if you want to preserve state across runs,
#      use `npm run local:stop-all` instead.
#   4. Best-effort `docker volume prune` for any orphaned ihcp/in-home
#      volumes left behind by an interrupted compose run.
#
# Safe to run when nothing is up: every step is a no-op if there's nothing
# to do.
set -uo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
DIR="$REPO/DevOps/Local"

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
echo "=== Bringing docker stacks down (with volumes) ==="
# We deliberately don't reuse docker-all-down.sh here because that script
# uses plain `docker compose down` which preserves volumes — fine for
# `local:stop-all`, wrong for shutdown. Inline the per-stack `down -v`
# so the contract is explicit and obvious in the diff.
COMPOSE_FILES=(
  "$DIR/Airflow/docker-compose.yml"
  "$DIR/Observability/Kibana/docker-compose.yml"
  "$DIR/Observability/Grafana/docker-compose.yml"
  "$DIR/Observability/Prometheus/docker-compose.yml"
  "$DIR/VectorDBs/pgvector/docker-compose.yml"
  "$DIR/VectorDBs/milvus/docker-compose.yml"
  "$DIR/VectorDBs/chroma/docker-compose.yml"
  "$DIR/VectorDBs/weaviate/docker-compose.yml"
  "$DIR/VectorDBs/qdrant/docker-compose.yml"
  "$DIR/Redis/docker-compose.yml"
  "$DIR/Postgres/docker-compose.yml"
  "$DIR/Kafka/docker-compose.yml"
  "$DIR/MongoDB/docker-compose.yml"
)
for compose in "${COMPOSE_FILES[@]}"; do
  if [ -f "$compose" ]; then
    echo "  down -v: $(basename "$(dirname "$compose")")"
    docker compose -f "$compose" down -v 2>&1 | sed 's/^/    /' || true
  fi
done

echo ""
echo "=== Removing shared network ==="
docker network rm in-home-care-network 2>/dev/null || echo "  (already removed)"

echo ""
echo "=== Pruning orphaned ihcp volumes ==="
# Catch volumes left behind by an interrupted compose run. Match by the
# in-home / ihcp / kafka / postgres prefixes the local stack creates.
ORPHANS="$(docker volume ls -q 2>/dev/null | grep -E '^(in-home|ihcp|kafka_kafka-data|postgres_postgres-data|mongodb_mongodb-data|redis_redis-data)' || true)"
if [ -n "$ORPHANS" ]; then
  echo "$ORPHANS" | while read -r vol; do
    docker volume rm "$vol" 2>/dev/null && echo "  removed $vol" || echo "  skipped $vol (in use?)"
  done
else
  echo "  (none)"
fi

echo ""
echo "Local stack fully shut down. All volumes wiped."
