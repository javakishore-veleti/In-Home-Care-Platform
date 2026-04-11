#!/usr/bin/env bash
# Status of the Docker containers used by the member portal journey.
DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Network ==="
docker network inspect in-home-care-network --format '{{.Name}}: {{len .Containers}} containers' 2>/dev/null || echo "  Network: not created"

echo ""
echo "=== Kafka ==="
docker compose -f "$DIR/Kafka/docker-compose.yml" ps 2>/dev/null || echo "  Kafka: not running"

echo ""
echo "=== Postgres ==="
docker compose -f "$DIR/Postgres/docker-compose.yml" ps 2>/dev/null || echo "  Postgres: not running"
