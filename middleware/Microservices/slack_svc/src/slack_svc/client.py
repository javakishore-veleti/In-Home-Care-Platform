"""HTTP client for appointment_svc.

slack_svc never touches the appointments DB directly. Every read/write goes
through this thin wrapper so the contract between the two services stays
visible in one place.
"""
from __future__ import annotations

import logging
import os
from typing import Any

import httpx

log = logging.getLogger(__name__)

APPOINTMENT_SVC_URL = os.getenv('APPOINTMENT_SVC_URL', 'http://127.0.0.1:8004')
API_GATEWAY_URL = os.getenv('API_GATEWAY_URL', 'http://127.0.0.1:8001')
HTTP_TIMEOUT = float(os.getenv('APPOINTMENT_SVC_TIMEOUT_SECONDS', '5'))


async def get_appointment(appointment_id: int) -> dict[str, Any] | None:
    """Fetch a single appointment. Returns None on 404 (deleted/never existed)."""
    url = f'{APPOINTMENT_SVC_URL}/appointments/{appointment_id}'
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            resp = await client.get(url)
    except httpx.HTTPError as exc:
        log.warning('appointment_svc.get_failed', extra={'id': appointment_id, 'error': str(exc)})
        raise
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()


async def attach_slack_message(
    appointment_id: int,
    slack_channel_id: str,
    slack_message_ts: str,
) -> dict[str, Any]:
    url = f'{APPOINTMENT_SVC_URL}/appointments/{appointment_id}/slack-message'
    payload = {'slack_channel_id': slack_channel_id, 'slack_message_ts': slack_message_ts}
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        resp = await client.patch(url, json=payload)
    resp.raise_for_status()
    return resp.json()


async def lookup_slack_integrations(event_type: str) -> list[dict[str, Any]]:
    """Ask api_gateway for *every* enabled channel mapped to ``event_type``.

    Returns the full list (possibly multiple channels for fan-out) or
    an empty list if nothing is configured / the gateway is unreachable.
    Callers fall back to their default channel constant when the list
    is empty so a transient gateway hiccup never blocks a Slack post.
    """
    url = f'{API_GATEWAY_URL}/api/internal/slack/integrations/lookup'
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            resp = await client.get(url, params={'event_type': event_type})
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        log.warning('slack_integration_lookup.failed event_type=%s error=%s', event_type, exc)
        return []
    body = resp.json()
    return body.get('integrations') or []


async def list_slack_posts(appointment_id: int) -> list[dict[str, Any]]:
    """Return every Slack channel this appointment has already been posted to."""
    url = f'{APPOINTMENT_SVC_URL}/appointments/{appointment_id}/slack-posts'
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            resp = await client.get(url)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        log.warning('slack_posts.list_failed id=%s error=%s', appointment_id, exc)
        return []
    return (resp.json() or {}).get('items') or []


async def claim_appointment(
    appointment_id: int,
    *,
    slack_user_id: str,
    slack_user_name: str | None,
    slack_team_id: str | None,
    slack_channel_id: str | None,
    slack_message_ts: str | None,
) -> dict[str, Any]:
    url = f'{APPOINTMENT_SVC_URL}/appointments/{appointment_id}/claim'
    payload = {
        'appointment_id': appointment_id,
        'slack_user_id': slack_user_id,
        'slack_user_name': slack_user_name,
        'slack_team_id': slack_team_id,
        'slack_channel_id': slack_channel_id,
        'slack_message_ts': slack_message_ts,
    }
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        resp = await client.post(url, json=payload)
    resp.raise_for_status()
    return resp.json()
