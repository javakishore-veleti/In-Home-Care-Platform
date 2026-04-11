#!/usr/bin/env bash
# Stop the Docker containers used by the member portal journey.
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Postgres ==="
docker compose -f "$DIR/Postgres/docker-compose.yml" down

echo "=== Kafka ==="
docker compose -f "$DIR/Kafka/docker-compose.yml" down

echo "=== Removing shared network ==="
docker network rm in-home-care-network 2>/dev/null || echo "Network already removed or still in use"

echo "Member-stack Docker containers down."
