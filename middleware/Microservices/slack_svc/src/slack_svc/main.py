"""slack_svc entrypoint — starts the Kafka consumer in a lifespan task."""
from __future__ import annotations

import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / 'middleware'))

# Python's default root logger level is WARNING which silently drops
# every INFO line from shared/kafka.py and slack_svc/consumer.py
# (kafka.consumer_started, slack_svc.fanout_done, etc.) — which made
# the Kafka consumer look "stuck" when it was actually working. Pin
# the relevant logger families to INFO so future diagnostics are
# visible in /tmp/ihcp_slack_svc.log without having to dig.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
)
logging.getLogger('slack_svc').setLevel(logging.INFO)
logging.getLogger('shared').setLevel(logging.INFO)
# aiokafka and kafka.* are very noisy at INFO — keep them at WARNING
# so they show the "coordinator dead" style transient warnings but not
# every poll.
logging.getLogger('aiokafka').setLevel(logging.WARNING)
logging.getLogger('kafka').setLevel(logging.WARNING)

from .consumer import start_consumer_task
from .routes import router


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
    application = FastAPI(title='slack_svc', version='0.1.0', lifespan=lifespan)
    application.include_router(router)

    @application.get('/healthz')
    def healthz() -> dict[str, str]:
        return {'status': 'ok'}

    @application.get('/version')
    def version() -> dict[str, str]:
        return {'service': 'slack_svc', 'version': '0.1.0'}

    return application


app = create_app()
