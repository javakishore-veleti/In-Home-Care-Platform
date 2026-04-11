"""collection_ingest_svc entrypoint — auto-migrates on startup."""
from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI

# Add shared module to path so auto_migrate is importable
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "middleware"))

from .api.deps import build_services
from .api.routes import init_routes, router


def create_app() -> FastAPI:
    # Auto-migrate this service's schema on every startup (idempotent)
    try:
        from shared.auto_migrate import run_migrations
        service_dir = Path(__file__).resolve().parent.parent.parent
        run_migrations(service_dir=service_dir)
    except Exception as e:
        print(f"[collection_ingest_svc] auto-migrate warning: {e}")

    app = FastAPI(title="collection-ingest-svc", version="0.1.0")

    col_svc, ingest_svc = build_services(use_fakes=True)
    init_routes(col_svc, ingest_svc)

    app.include_router(router)

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    return app


app = create_app()
