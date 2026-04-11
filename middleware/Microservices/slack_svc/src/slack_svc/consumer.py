"""Kafka consumer that turns appointment events into Slack messages.

Flow per message:
  1. Re-fetch the appointment from appointment_svc by id (so a delete or
     status change between produce and consume is observed *now*, not at
     produce time).
  2. If it's gone (404) or already cancelled, log and commit — nothing to
     post.
  3. If it already has a `slack_message_ts`, this is a redelivery — skip
     and commit so we never post twice.
  4. Otherwise post the Block Kit message and PATCH the appointment with
     the returned `channel` + `ts` to mark it posted.
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

import httpx

from shared.events import APPOINTMENT_BOOKED, APPOINTMENT_EVENTS_TOPIC
from shared.kafka import run_consumer
from shared.slack import post_message

from . import client
from .blocks import appointment_request

log = logging.getLogger(__name__)

CONSUMER_GROUP = os.getenv('SLACK_SVC_CONSUMER_GROUP', 'slack_svc.appointments')
APPOINTMENT_REQUESTS_CHANNEL = os.getenv(
    'SLACK_APPOINTMENT_REQUESTS_CHANNEL',
    'in-home-help-member-appointment-requests',
)


async def handle_appointment_event(event: dict[str, Any]) -> bool:
    event_type = event.get('event_type')
    appointment_id = event.get('appointment_id')

    if event_type != APPOINTMENT_BOOKED:
        log.info('slack_svc.event_ignored', extra={'event_type': event_type})
        return True
    if not appointment_id:
        log.warning('slack_svc.event_missing_id', extra={'event': event})
        return True

    try:
        appointment = await client.get_appointment(int(appointment_id))
    except httpx.HTTPError:
        # Transient appointment_svc failure — leave offset uncommitted, retry next poll.
        return False

    if appointment is None:
        log.info('slack_svc.appointment_gone', extra={'appointment_id': appointment_id})
        return True

    if (appointment.get('status') or '').lower() == 'cancelled':
        log.info('slack_svc.appointment_cancelled', extra={'appointment_id': appointment_id})
        return True

    if appointment.get('slack_message_ts'):
        log.info('slack_svc.dedup_skip', extra={'appointment_id': appointment_id})
        return True

    text, blocks = appointment_request(appointment)
    result = post_message(APPOINTMENT_REQUESTS_CHANNEL, text=text, blocks=blocks)
    if not result or not result.get('ok'):
        # Slack down or rate-limited — let Kafka redeliver.
        log.warning(
            'slack_svc.post_failed',
            extra={'appointment_id': appointment_id, 'slack_error': (result or {}).get('error')},
        )
        return False

    channel_id = result.get('channel')
    ts = result.get('ts')
    if not channel_id or not ts:
        log.warning('slack_svc.post_no_ts', extra={'appointment_id': appointment_id, 'result': result})
        return True

    try:
        await client.attach_slack_message(int(appointment_id), channel_id, ts)
    except httpx.HTTPError as exc:
        # Slack post succeeded but we failed to record the ts. Don't redeliver
        # (would post twice). Log loudly so this can be reconciled.
        log.error(
            'slack_svc.attach_message_failed',
            extra={'appointment_id': appointment_id, 'channel_id': channel_id, 'ts': ts, 'error': str(exc)},
        )
    return True


async def start_consumer_task(stop_event: asyncio.Event) -> None:
    await run_consumer(
        topic=APPOINTMENT_EVENTS_TOPIC,
        group_id=CONSUMER_GROUP,
        handler=handle_appointment_event,
        stop_event=stop_event,
    )
