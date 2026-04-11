#!/usr/bin/env bash
# Show the current Alembic revision for every microservice schema.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
VENV="$HOME/runtime_data/python_venvs/In-Home-Care-Platform"
ALEMBIC="$VENV/bin/alembic"

SERVICES="auth_svc member_svc appointment_svc visit_management_svc visit_ingest_svc document_intelligence_svc collection_ingest_svc"

echo "=== Database migration status ==="
echo ""
printf "  %-35s %-15s %s\n" "Service" "Schema" "Current revision"
printf "  %-35s %-15s %s\n" "---" "---" "---"

for svc in $SERVICES; do
  SVC_DIR="$REPO_ROOT/middleware/Microservices/$svc"
  if [ -f "$SVC_DIR/alembic.ini" ]; then
    cd "$SVC_DIR"
    REV=$("$ALEMBIC" current 2>/dev/null | head -1 || echo "not migrated")
    SCHEMA=$(grep "^SCHEMA" alembic/env.py | head -1 | cut -d'"' -f2)
    printf "  %-35s %-15s %s\n" "$svc" "$SCHEMA" "$REV"
    cd "$REPO_ROOT"
  fi
done
echo ""
