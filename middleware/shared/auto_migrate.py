"""Auto-migrate on service startup.

Every microservice calls run_migrations() from its main.py / lifespan
handler so schema migrations run automatically on every deploy — whether
locally via npm, in a Docker container, or on AWS ECS/EKS. The migration
is idempotent: Alembic checks the version table and skips if already at
head.

Usage in any microservice main.py:

    from shared.auto_migrate import run_migrations

    def create_app():
        run_migrations(service_dir=Path(__file__).resolve().parent.parent.parent)
        ...

Or in a lifespan handler:

    @asynccontextmanager
    async def lifespan(app):
        run_migrations(service_dir=...)
        yield
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import structlog

log = structlog.get_logger(__name__)


def run_migrations(
    *,
    service_dir: Path | str | None = None,
    alembic_ini: str = "alembic.ini",
) -> None:
    """Run `alembic upgrade head` for one microservice.

    service_dir: the root of the microservice folder (where alembic.ini lives).
                 If None, auto-detected from the caller's __file__.
    """
    svc_dir = Path(service_dir) if service_dir else _detect_service_dir()
    ini_path = svc_dir / alembic_ini

    if not ini_path.exists():
        log.warning("auto_migrate.skip", reason="no alembic.ini", path=str(ini_path))
        return

    log.info("auto_migrate.start", service_dir=str(svc_dir))

    try:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=str(svc_dir),
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            log.info("auto_migrate.done", output=result.stdout.strip())
        else:
            log.error(
                "auto_migrate.failed",
                returncode=result.returncode,
                stderr=result.stderr.strip(),
            )
    except subprocess.TimeoutExpired:
        log.error("auto_migrate.timeout", service_dir=str(svc_dir))
    except FileNotFoundError:
        log.warning("auto_migrate.alembic_not_installed")


def _detect_service_dir() -> Path:
    """Walk up from the caller's frame to find alembic.ini."""
    import inspect

    frame = inspect.stack()[2]
    caller_file = Path(frame.filename).resolve()
    # Walk up until we find alembic.ini
    for parent in [caller_file.parent] + list(caller_file.parents):
        if (parent / "alembic.ini").exists():
            return parent
    return caller_file.parent
