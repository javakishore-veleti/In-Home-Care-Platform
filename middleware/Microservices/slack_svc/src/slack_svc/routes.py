"""HTTP endpoints for inbound Slack traffic.

Two webhooks:
  - POST /slack/interactivity — Block Kit button clicks (Claim button).
  - POST /slack/events        — Slack Events API (URL verification + log).

Both verify the Slack request signature using SLACK_SIGNING_SECRET.
"""
from __future__ import annotations

import json
import logging
import urllib.parse
from typing import Any

from fastapi import APIRouter, HTTPException, Request, status

from shared.slack import update_message, verify_signature

from . import client
from .blocks import appointment_claimed, appointment_unavailable
from .consumer import APPOINTMENT_REQUESTS_CHANNEL  # reuse the same default channel

log = logging.getLogger(__name__)

router = APIRouter(tags=['slack'])


async def _read_and_verify(request: Request) -> bytes:
    raw = await request.body()
    headers = {k.lower(): v for k, v in request.headers.items()}
    if not verify_signature(headers, raw):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid Slack signature.')
    return raw


@router.post('/slack/interactivity')
async def slack_interactivity(request: Request) -> dict[str, Any]:
    raw = await _read_and_verify(request)
    form = urllib.parse.parse_qs(raw.decode('utf-8'))
    payload_str = (form.get('payload') or [''])[0]
    if not payload_str:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Missing payload.')
    try:
        payload = json.loads(payload_str)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'Bad payload: {exc}')

    actions = payload.get('actions') or []
    if not actions:
        return {'ok': True}
    action = actions[0]
    action_id = action.get('action_id')
    if action_id != 'claim_appointment':
        log.info('slack_svc.unknown_action', extra={'action_id': action_id})
        return {'ok': True}

    try:
        appointment_id = int(action.get('value'))
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Bad appointment id.')

    user = payload.get('user') or {}
    team = payload.get('team') or {}
    channel = payload.get('channel') or {}
    message = payload.get('message') or {}
    slack_user_id = user.get('id') or ''
    slack_user_name = user.get('username') or user.get('name')
    slack_team_id = team.get('id')
    slack_channel_id = channel.get('id')
    slack_message_ts = message.get('ts')

    appointment = await client.get_appointment(appointment_id)
    if appointment is None:
        text, blocks = appointment_unavailable(appointment_id, 'no longer exists')
        if slack_channel_id and slack_message_ts:
            update_message(slack_channel_id, slack_message_ts, text=text, blocks=blocks)
        return {'ok': True}

    result = await client.claim_appointment(
        appointment_id,
        slack_user_id=slack_user_id,
        slack_user_name=slack_user_name,
        slack_team_id=slack_team_id,
        slack_channel_id=slack_channel_id,
        slack_message_ts=slack_message_ts,
    )

    appt = result.get('appointment') or appointment
    text, blocks = appointment_claimed(appt, slack_user_id)
    if slack_channel_id and slack_message_ts:
        update_message(slack_channel_id, slack_message_ts, text=text, blocks=blocks)
    return {'ok': True, 'already_claimed': result.get('already_claimed', False)}


@router.post('/slack/events')
async def slack_events(request: Request) -> dict[str, Any]:
    raw = await _read_and_verify(request)
    try:
        body = json.loads(raw.decode('utf-8'))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'Bad JSON: {exc}')
    if body.get('type') == 'url_verification':
        return {'challenge': body.get('challenge', '')}
    event = body.get('event') or {}
    event_type = event.get('type', '')
    log.info('slack_svc.event type=%s event_type=%s', body.get('type'), event_type)

    # Interactive Q&A: if a user replies in a thread, check if it's a
    # briefing thread and dispatch to the knowledge agent for a follow-up answer.
    if event_type == 'message' and event.get('thread_ts') and not event.get('bot_id'):
        import os, httpx
        channel_id = event.get('channel', '')
        thread_ts = event.get('thread_ts', '')
        user_text = event.get('text', '')
        user_id = event.get('user', '')
        if user_text and channel_id and thread_ts:
            log.info('slack_svc.thread_reply channel=%s thread_ts=%s user=%s text=%s',
                     channel_id, thread_ts, user_id, user_text[:100])
            # Best-effort: call the knowledge agent's Q&A endpoint
            agent_url = os.getenv('KNOWLEDGE_AGENT_URL', 'http://127.0.0.1:8011')
            try:
                async with httpx.AsyncClient(timeout=30) as hc:
                    await hc.post(f'{agent_url}/qa', json={
                        'channel_id': channel_id,
                        'thread_ts': thread_ts,
                        'user_text': user_text,
                        'user_id': user_id,
                    })
            except Exception as exc:
                log.warning('slack_svc.qa_dispatch_failed error=%s', exc)

    return {'ok': True}
