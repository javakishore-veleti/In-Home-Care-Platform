"""collection_ingest_svc entrypoint."""
from __future__ import annotations

from fastapi import FastAPI

from .api.deps import build_services
from .api.routes import init_routes, router


def create_app() -> FastAPI:
    app = FastAPI(title="collection-ingest-svc", version="0.1.0")

    col_svc, ingest_svc = build_services(use_fakes=True)
    init_routes(col_svc, ingest_svc)

    app.include_router(router)

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    return app


app = create_app()
