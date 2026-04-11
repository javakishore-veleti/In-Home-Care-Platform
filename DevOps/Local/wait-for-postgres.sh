#!/usr/bin/env bash
#
# Block until the in-home-care-postgres container is ready to accept
# queries. `docker compose up -d` returns as soon as the container is
# *created* — not when initdb has finished and the server is ready —
# so any caller that runs alembic immediately after compose up will
# race the database and get
#
#   server closed the connection unexpectedly
#
# This script gates that race by polling `pg_isready` from inside the
# container itself (no host-side `pg_isready` dependency).
set -uo pipefail

CONTAINER="${POSTGRES_CONTAINER:-in-home-care-postgres}"
USER="${POSTGRES_USER:-care}"
DB="${POSTGRES_DB:-in_home_care_platform}"
TIMEOUT="${POSTGRES_WAIT_TIMEOUT:-60}"

if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
  echo "wait-for-postgres: container '${CONTAINER}' is not running."
  exit 1
fi

echo "wait-for-postgres: waiting up to ${TIMEOUT}s for ${CONTAINER}..."
for i in $(seq 1 "${TIMEOUT}"); do
  if docker exec "${CONTAINER}" pg_isready -U "${USER}" -d "${DB}" >/dev/null 2>&1; then
    echo "wait-for-postgres: ready after ${i}s"
    exit 0
  fi
  sleep 1
done

echo "wait-for-postgres: timed out after ${TIMEOUT}s"
docker logs "${CONTAINER}" --tail 30 2>&1 | sed 's/^/  /'
exit 1
