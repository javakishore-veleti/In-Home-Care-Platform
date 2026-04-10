#!/usr/bin/env bash
DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Core infrastructure ==="
docker compose -f "$DIR/MongoDB/docker-compose.yml" ps 2>/dev/null || echo "  MongoDB: not running"
docker compose -f "$DIR/Kafka/docker-compose.yml" ps 2>/dev/null || echo "  Kafka: not running"

echo ""
echo "=== Extras ==="
docker compose -f "$DIR/Postgres/docker-compose.yml" ps 2>/dev/null || echo "  Postgres: not running"
docker compose -f "$DIR/Redis/docker-compose.yml" ps 2>/dev/null || echo "  Redis: not running"

echo ""
echo "=== VectorDBs ==="
for db in qdrant weaviate chroma milvus pgvector; do
  if [ -f "$DIR/VectorDBs/$db/docker-compose.yml" ]; then
    echo "--- $db ---"
    docker compose -f "$DIR/VectorDBs/$db/docker-compose.yml" ps 2>/dev/null || echo "  $db: not running"
  fi
done

echo ""
echo "=== Observability ==="
docker compose -f "$DIR/Observability/Prometheus/docker-compose.yml" ps 2>/dev/null || echo "  Prometheus: not running"
docker compose -f "$DIR/Observability/Grafana/docker-compose.yml" ps 2>/dev/null || echo "  Grafana: not running"
docker compose -f "$DIR/Observability/Kibana/docker-compose.yml" ps 2>/dev/null || echo "  Kibana: not running"
