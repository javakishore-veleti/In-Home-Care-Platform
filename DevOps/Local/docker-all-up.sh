#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Core infrastructure ==="
docker compose -f "$DIR/MongoDB/docker-compose.yml" up -d
docker compose -f "$DIR/Kafka/docker-compose.yml" up -d

echo "=== Extras ==="
docker compose -f "$DIR/Postgres/docker-compose.yml" up -d
docker compose -f "$DIR/Redis/docker-compose.yml" up -d

echo "=== VectorDBs ==="
for db in qdrant weaviate chroma milvus pgvector; do
  if [ -f "$DIR/VectorDBs/$db/docker-compose.yml" ]; then
    docker compose -f "$DIR/VectorDBs/$db/docker-compose.yml" up -d
  fi
done

echo "=== Observability ==="
docker compose -f "$DIR/Observability/Prometheus/docker-compose.yml" up -d
docker compose -f "$DIR/Observability/Grafana/docker-compose.yml" up -d
docker compose -f "$DIR/Observability/Kibana/docker-compose.yml" up -d

echo "All stacks up."
