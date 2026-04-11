from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
MICROSERVICE_ROOT = REPO_ROOT / 'middleware' / 'Microservices'
for path in [
    REPO_ROOT / 'middleware',
    MICROSERVICE_ROOT / 'auth_svc' / 'src',
    MICROSERVICE_ROOT / 'member_svc' / 'src',
    MICROSERVICE_ROOT / 'appointment_svc' / 'src',
    MICROSERVICE_ROOT / 'visit_management_svc' / 'src',
]:
    sys.path.insert(0, str(path))

from .admin_routes import router as admin_router
from .auth import router as auth_router
from .member_routes import router as member_router
from .support_routes import router as support_router


def create_app() -> FastAPI:
    try:
        from shared.auto_migrate import run_migrations

        service_dir = Path(__file__).resolve().parent.parent.parent
        run_migrations(service_dir=service_dir)
    except Exception as exc:  # pragma: no cover
        print(f'[api_gateway] auto-migrate warning: {exc}')

    application = FastAPI(title='api_gateway', version='0.1.0')
    application.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )
    application.include_router(auth_router)
    application.include_router(member_router)
    application.include_router(admin_router)
    application.include_router(support_router)

    @application.get('/healthz')
    def healthz() -> dict[str, str]:
        return {'status': 'ok'}

    @application.get('/version')
    def version() -> dict[str, str]:
        return {'service': 'api_gateway', 'version': '0.1.0'}

    return application


app = create_app()
