#!/usr/bin/env bash
# Start only the Docker containers needed for the member portal journey:
#   Kafka  — event bus
#   Postgres — relational store for auth, member, appointment, visit schemas
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Creating shared network ==="
docker network create in-home-care-network 2>/dev/null || echo "Network in-home-care-network already exists"

echo "=== Kafka ==="
docker compose -f "$DIR/Kafka/docker-compose.yml" up -d
docker compose -f "$DIR/KafkaUI/docker-compose.yml" up -d

echo "=== Postgres ==="
docker compose -f "$DIR/Postgres/docker-compose.yml" up -d

echo "=== Waiting for Postgres to accept queries ==="
bash "$DIR/wait-for-postgres.sh"

echo "=== Waiting for Kafka to accept consumer-group traffic ==="
bash "$DIR/wait-for-kafka.sh"

echo "Member-stack Docker containers up on network: in-home-care-network"
