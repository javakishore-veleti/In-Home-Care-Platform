"""visit_management_svc entrypoint — auto-migrates on startup."""
from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI

# Add shared module to path so auto_migrate is importable
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "middleware"))


def create_app() -> FastAPI:
    # Auto-migrate this service's schema on every startup (idempotent)
    try:
        from shared.auto_migrate import run_migrations
        service_dir = Path(__file__).resolve().parent.parent
        run_migrations(service_dir=service_dir)
    except Exception as e:
        print(f"[visit_management_svc] auto-migrate warning: {e}")

    application = FastAPI(title="visit_management_svc", version="0.1.0")

    @application.get("/healthz")
    def healthz():
        return {"status": "ok"}

    @application.get("/version")
    def version():
        return {"service": "visit_management_svc", "version": "0.1.0"}

    return application


app = create_app()
