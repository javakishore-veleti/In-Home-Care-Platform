#!/usr/bin/env bash
#
# Block until the in-home-care-kafka container is ready to accept
# consumer-group traffic. `docker compose up -d` returns as soon as
# the container is *created*, not when the broker has finished its
# KRaft bootstrap and the __consumer_offsets internal topic is ready.
# Any slack_svc / aiokafka consumer that connects before that point
# ends up in a "GroupCoordinatorNotAvailable → Marking the coordinator
# dead" loop that retries internally but never surfaces as a clean
# success, which is exactly the race we keep hitting.
#
# Strategy: poll the broker via `kafka-broker-api-versions.sh` inside
# the container. It returns successfully only when the broker is
# fully up and advertising its listeners — which happens *after*
# __consumer_offsets is ready.
set -uo pipefail

CONTAINER="${KAFKA_CONTAINER:-in-home-care-kafka}"
TIMEOUT="${KAFKA_WAIT_TIMEOUT:-60}"

if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
  echo "wait-for-kafka: container '${CONTAINER}' is not running."
  exit 1
fi

echo "wait-for-kafka: waiting up to ${TIMEOUT}s for ${CONTAINER}..."
for i in $(seq 1 "${TIMEOUT}"); do
  # apache/kafka 3.9 image ships the scripts under /opt/kafka/bin/.
  # The command exits 0 only when the broker is ready to serve
  # metadata requests — which is what aiokafka's .start() needs.
  if docker exec "${CONTAINER}" \
      /opt/kafka/bin/kafka-broker-api-versions.sh \
      --bootstrap-server localhost:9092 >/dev/null 2>&1; then
    echo "wait-for-kafka: ready after ${i}s"
    exit 0
  fi
  sleep 1
done

echo "wait-for-kafka: timed out after ${TIMEOUT}s"
docker logs "${CONTAINER}" --tail 30 2>&1 | sed 's/^/  /'
exit 1
