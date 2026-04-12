"""Kafka consumer for appointment.claimed events.

Subscribes to appointment.events, filters for event_type ==
appointment.claimed, and dispatches each to the briefing flow.
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

from shared.events import APPOINTMENT_CLAIMED, APPOINTMENT_EVENTS_TOPIC
from shared.kafka import run_consumer

from .briefing import run_briefing

log = logging.getLogger(__name__)

CONSUMER_GROUP = os.getenv('KNOWLEDGE_AGENT_CONSUMER_GROUP', 'knowledge_agent_svc.briefings')


async def handle_event(event: dict[str, Any]) -> bool:
    event_type = event.get('event_type')
    if event_type != APPOINTMENT_CLAIMED:
        return True
    return await run_briefing(event)


async def start_consumer_task(stop_event: asyncio.Event) -> None:
    await run_consumer(
        topic=APPOINTMENT_EVENTS_TOPIC,
        group_id=CONSUMER_GROUP,
        handler=handle_event,
        stop_event=stop_event,
    )
