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

    text, blocks = appointment_request(appointment)

    # Resolve the destination channel set from the admin-managed
    # integrations table. Fan-out: every enabled row receives the post.
    # Empty list (no rows configured) -> fall back to env var default
    # so a fresh DB still works without any UI configuration.
    integrations = await client.lookup_slack_integrations(APPOINTMENT_BOOKED)
    if not integrations:
        targets = [{'slack_channel_id': APPOINTMENT_REQUESTS_CHANNEL, 'slack_channel_name': APPOINTMENT_REQUESTS_CHANNEL}]
    else:
        targets = integrations

    # Per-channel dedupe via the appointment_slack_posts table — a
    # Kafka redelivery never re-posts to a channel it already hit.
    already_posted = {row.get('slack_channel_id') for row in await client.list_slack_posts(int(appointment_id))}

    any_failure = False
    posted_count = 0
    for target in targets:
        target_channel = target.get('slack_channel_id')
        if not target_channel:
            continue
        if target_channel in already_posted:
            log.info(
                'slack_svc.dedup_skip appointment_id=%s channel=%s',
                appointment_id,
                target_channel,
            )
            continue
        result = post_message(target_channel, text=text, blocks=blocks)
        if not result or not result.get('ok'):
            log.warning(
                'slack_svc.post_failed appointment_id=%s channel=%s slack_error=%s',
                appointment_id,
                target_channel,
                (result or {}).get('error'),
            )
            any_failure = True
            continue
        landed_channel = result.get('channel') or target_channel
        ts = result.get('ts')
        if not ts:
            log.warning('slack_svc.post_no_ts appointment_id=%s channel=%s', appointment_id, landed_channel)
            continue
        try:
            await client.attach_slack_message(int(appointment_id), landed_channel, ts)
            posted_count += 1
        except httpx.HTTPError as exc:
            # Slack post succeeded but we failed to record the post.
            # Don't redeliver (would post twice). Log loudly so this
            # can be reconciled — the dedupe table is now out of sync
            # with reality for this (appointment, channel) pair.
            log.error(
                'slack_svc.attach_message_failed appointment_id=%s channel=%s ts=%s error=%s',
                appointment_id,
                landed_channel,
                ts,
                str(exc),
            )

    log.info(
        'slack_svc.fanout_done appointment_id=%s posted=%s targets=%s already=%s',
        appointment_id,
        posted_count,
        len(targets),
        len(already_posted),
    )
    # Returning False forces Kafka to redeliver the entire message,
    # which the dedupe table will then handle gracefully (skipping
    # channels that already landed). Only do that on a real Slack
    # failure so a partial fan-out gets a second chance.
    return not any_failure


async def start_consumer_task(stop_event: asyncio.Event) -> None:
    await run_consumer(
        topic=APPOINTMENT_EVENTS_TOPIC,
        group_id=CONSUMER_GROUP,
        handler=handle_appointment_event,
        stop_event=stop_event,
    )
