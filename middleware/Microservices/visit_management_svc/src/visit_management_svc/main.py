from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / 'middleware'))

from .routes import router


def create_app() -> FastAPI:
    try:
        from shared.auto_migrate import run_migrations

        service_dir = Path(__file__).resolve().parent.parent.parent
        run_migrations(service_dir=service_dir)
    except Exception as exc:  # pragma: no cover
        print(f'[visit_management_svc] auto-migrate warning: {exc}')

    application = FastAPI(title='visit_management_svc', version='0.1.0')
    application.include_router(router)

    @application.get('/healthz')
    def healthz() -> dict[str, str]:
        return {'status': 'ok'}

    @application.get('/version')
    def version() -> dict[str, str]:
        return {'service': 'visit_management_svc', 'version': '0.1.0'}

    return application


app = create_app()
