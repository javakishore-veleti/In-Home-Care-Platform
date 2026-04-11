from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / 'middleware'))

from .routes import router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield
    try:
        from shared.kafka import stop_producer

        await stop_producer()
    except Exception as exc:  # pragma: no cover
        print(f'[appointment_svc] kafka stop_producer warning: {exc}')


def create_app() -> FastAPI:
    try:
        from shared.auto_migrate import run_migrations

        service_dir = Path(__file__).resolve().parent.parent.parent
        run_migrations(service_dir=service_dir)
    except Exception as exc:  # pragma: no cover
        print(f'[appointment_svc] auto-migrate warning: {exc}')

    application = FastAPI(title='appointment_svc', version='0.1.0', lifespan=lifespan)
    application.include_router(router)

    @application.get('/healthz')
    def healthz() -> dict[str, str]:
        return {'status': 'ok'}

    @application.get('/version')
    def version() -> dict[str, str]:
        return {'service': 'appointment_svc', 'version': '0.1.0'}

    return application


app = create_app()
