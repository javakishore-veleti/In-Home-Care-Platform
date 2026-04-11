#!/usr/bin/env bash
# Run Alembic migrations for every microservice that owns a schema.
# Each service migrates into its own schema inside the shared
# in_home_care_platform Postgres database.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
VENV="$HOME/runtime_data/python_venvs/In-Home-Care-Platform"
ALEMBIC="$VENV/bin/alembic"

if [ ! -f "$ALEMBIC" ]; then
  echo "ERROR: Alembic not found at $ALEMBIC"
  echo "Run: npm run setup:local:venv:install"
  exit 1
fi

SERVICES="auth_svc member_svc appointment_svc visit_management_svc visit_ingest_svc document_intelligence_svc collection_ingest_svc"

echo "=== Creating database if needed ==="
PGPASSWORD=care psql -h localhost -U care -d postgres -c "CREATE DATABASE in_home_care_platform" 2>/dev/null || echo "Database in_home_care_platform already exists"

echo ""
echo "=== Running migrations ==="
for svc in $SERVICES; do
  SVC_DIR="$REPO_ROOT/middleware/Microservices/$svc"
  if [ -f "$SVC_DIR/alembic.ini" ]; then
    echo "--- $svc ---"
    cd "$SVC_DIR"
    "$ALEMBIC" upgrade head 2>&1 | sed 's/^/  /'
    cd "$REPO_ROOT"
  fi
done

echo ""
echo "=== All migrations complete ==="
