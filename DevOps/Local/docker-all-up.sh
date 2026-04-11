#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Creating shared network ==="
docker network create in-home-care-network 2>/dev/null || echo "Network in-home-care-network already exists"

echo "=== Core infrastructure ==="
docker compose -f "$DIR/Kafka/docker-compose.yml" up -d
docker compose -f "$DIR/KafkaUI/docker-compose.yml" up -d
# docker compose -f "$DIR/MongoDB/docker-compose.yml" up -d

echo "=== Extras ==="
docker compose -f "$DIR/Postgres/docker-compose.yml" up -d
# docker compose -f "$DIR/Redis/docker-compose.yml" up -d

echo "=== VectorDBs ==="
# for db in qdrant weaviate chroma milvus pgvector; do
#   if [ -f "$DIR/VectorDBs/$db/docker-compose.yml" ]; then
#     docker compose -f "$DIR/VectorDBs/$db/docker-compose.yml" up -d
#   fi
# done

echo "=== Observability ==="
# docker compose -f "$DIR/Observability/Prometheus/docker-compose.yml" up -d
# docker compose -f "$DIR/Observability/Grafana/docker-compose.yml" up -d
# docker compose -f "$DIR/Observability/Kibana/docker-compose.yml" up -d

echo "=== Airflow ==="
# docker compose -f "$DIR/Airflow/docker-compose.yml" up -d

echo "=== Waiting for Postgres to accept queries ==="
bash "$DIR/wait-for-postgres.sh"

echo "All stacks up on network: in-home-care-network"
