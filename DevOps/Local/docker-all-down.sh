#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
echo "=== Airflow ==="
docker compose -f "$DIR/Airflow/docker-compose.yml" down


echo "=== Observability ==="
docker compose -f "$DIR/Observability/Kibana/docker-compose.yml" down
docker compose -f "$DIR/Observability/Grafana/docker-compose.yml" down
docker compose -f "$DIR/Observability/Prometheus/docker-compose.yml" down

echo "=== VectorDBs ==="
for db in pgvector milvus chroma weaviate qdrant; do
  if [ -f "$DIR/VectorDBs/$db/docker-compose.yml" ]; then
    docker compose -f "$DIR/VectorDBs/$db/docker-compose.yml" down
  fi
done

echo "=== Extras ==="
docker compose -f "$DIR/Redis/docker-compose.yml" down
docker compose -f "$DIR/Postgres/docker-compose.yml" down

echo "=== Core infrastructure ==="
docker compose -f "$DIR/Kafka/docker-compose.yml" down
docker compose -f "$DIR/MongoDB/docker-compose.yml" down

echo "All stacks down."
