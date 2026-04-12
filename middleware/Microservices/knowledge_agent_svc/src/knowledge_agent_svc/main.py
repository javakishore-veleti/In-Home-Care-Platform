"""knowledge_agent_svc — LLM briefing agent triggered on appointment claims."""
from __future__ import annotations

import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / 'middleware'))

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s')
logging.getLogger('aiokafka').setLevel(logging.WARNING)
logging.getLogger('kafka').setLevel(logging.WARNING)

from .consumer import start_consumer_task


@asynccontextmanager
async def lifespan(_app: FastAPI):
    stop_event = asyncio.Event()
    consumer_task = asyncio.create_task(start_consumer_task(stop_event))
    try:
        yield
    finally:
        stop_event.set()
        try:
            await asyncio.wait_for(consumer_task, timeout=10)
        except asyncio.TimeoutError:
            consumer_task.cancel()


def create_app() -> FastAPI:
    from prometheus_client import make_asgi_app as prom_asgi
    from starlette.routing import Mount

    application = FastAPI(title='knowledge_agent_svc', version='0.1.0', lifespan=lifespan)
    application.mount('/metrics', prom_asgi())

    @application.get('/healthz')
    def healthz() -> dict[str, str]:
        return {'status': 'ok'}

    @application.get('/version')
    def version() -> dict[str, str]:
        return {'service': 'knowledge_agent_svc', 'version': '0.1.0'}

    return application


app = create_app()
