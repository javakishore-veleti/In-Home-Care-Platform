"""Cross-member endpoints for the care_admin_portal.

All endpoints in this router are gated by ``require_roles({'admin'})`` —
field officers, support, and members get a 403. The router is intentionally
read-mostly: admins inspect the system, mutations should still flow through
the relevant domain service.
"""
from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, status
from pydantic import BaseModel, Field

from shared import slack as slack_helpers

from .dependencies import (
    get_appointment_client,
    get_auth_store,
    get_member_store,
    get_slack_integration_store,
    get_visit_store,
    require_roles,
)

router = APIRouter(
    prefix='/api/admin',
    tags=['admin'],
    dependencies=[Depends(require_roles({'admin'}))],
)


@router.get('/dashboard/stats')
def dashboard_stats(
    member_store=Depends(get_member_store),
    visit_store=Depends(get_visit_store),
    appointment_client=Depends(get_appointment_client),
) -> dict[str, Any]:
    """Counts that drive the admin dashboard cards.

    Each ``total`` is a free side-effect of asking for page 1 with size 1, so
    we get the count without scanning rows we won't render.
    """
    open_appts = appointment_client.list_all_appointments(status_filter='requested', page=1, page_size=1)
    claimed_appts = appointment_client.list_all_appointments(status_filter='claimed', page=1, page_size=1)
    cancelled_appts = appointment_client.list_all_appointments(status_filter='cancelled', page=1, page_size=1)
    members = member_store.list_all_members(page=1, page_size=1)
    visits_today_total = 0
    try:
        all_visits = visit_store.list_all_visits(page=1, page_size=100)
        today = date.today()
        visits_today_total = sum(
            1 for v in all_visits['items'] if str(v.get('visit_date') or '').startswith(today.isoformat())
        )
    except Exception:  # pragma: no cover
        visits_today_total = 0
    return {
        'open_appointments': open_appts['total'],
        'claimed_appointments': claimed_appts['total'],
        'cancelled_appointments': cancelled_appts['total'],
        'total_members': members['total'],
        'todays_visits': visits_today_total,
    }


@router.get('/members')
def list_members(
    query: str | None = None,
    page: int = 1,
    page_size: int = 20,
    member_store=Depends(get_member_store),
) -> dict[str, Any]:
    return member_store.list_all_members(query=query, page=page, page_size=page_size)


@router.get('/appointments')
def list_appointments(
    query: str | None = None,
    status_filter: str | None = None,
    page: int = 1,
    page_size: int = 20,
    appointment_client=Depends(get_appointment_client),
) -> dict[str, Any]:
    return appointment_client.list_all_appointments(
        query=query,
        status_filter=status_filter,
        page=page,
        page_size=page_size,
    )


@router.get('/visits')
def list_visits(
    query: str | None = None,
    status_filter: str | None = None,
    page: int = 1,
    page_size: int = 20,
    visit_store=Depends(get_visit_store),
) -> dict[str, Any]:
    return visit_store.list_all_visits(
        query=query,
        status_filter=status_filter,
        page=page,
        page_size=page_size,
    )


@router.get('/claims')
def list_claims(
    page: int = 1,
    page_size: int = 20,
    appointment_client=Depends(get_appointment_client),
) -> dict[str, Any]:
    """All claimed appointments. Filtered server-side via status='claimed'."""
    return appointment_client.list_all_appointments(
        status_filter='claimed',
        page=page,
        page_size=page_size,
    )


@router.get('/staff')
def list_staff(auth_store=Depends(get_auth_store)) -> dict[str, Any]:
    staff = auth_store.list_users_by_roles(
        ['admin', 'support', 'field_officer', 'care_planner', 'auditor'],
    )
    return {'items': staff, 'total': len(staff)}


@router.get('/appointments/{appointment_id}')
def get_appointment(
    appointment_id: int,
    appointment_client=Depends(get_appointment_client),
) -> dict[str, Any]:
    return appointment_client.get_appointment(appointment_id)


@router.get('/members/{member_id}')
def get_member(member_id: int, member_store=Depends(get_member_store)) -> dict[str, Any]:
    return member_store.get_member(member_id)


@router.get('/visits/{visit_id}')
def get_visit(visit_id: int, visit_store=Depends(get_visit_store)) -> dict[str, Any]:
    return visit_store.get_visit(visit_id)


# ----- Slack channel integrations --------------------------------------
# These endpoints power the admin portal's "Slack Integrations" page.
# The page lets an admin map an event_type (e.g. appointment.booked) to
# a Slack channel without redeploying or editing env. slack_svc consults
# this same store via the unauthenticated /api/internal lookup endpoint.

class SlackIntegrationCreate(BaseModel):
    slack_channel_id: str = Field(min_length=1, max_length=64)
    slack_channel_name: str = Field(min_length=1, max_length=255)
    event_type: str = Field(min_length=1, max_length=100)


class SlackIntegrationToggle(BaseModel):
    enabled: bool


@router.get('/slack/channels')
def list_slack_channels(slack_integration_store=Depends(get_slack_integration_store)) -> dict[str, Any]:
    """List every Slack channel the bot can see, annotated with the
    integrations already wired against each. Falls back to an empty list
    on Slack API failure so the page renders an actionable empty state."""
    channels = slack_helpers.list_channels()
    integrations = slack_integration_store.list_integrations()
    by_channel: dict[str, list[dict[str, Any]]] = {}
    for integ in integrations:
        by_channel.setdefault(integ['slack_channel_id'], []).append(integ)
    rows: list[dict[str, Any]] = []
    for ch in channels:
        rows.append({
            'id': ch.get('id'),
            'name': ch.get('name'),
            'is_member': bool(ch.get('is_member')),
            'is_private': bool(ch.get('is_private')),
            'is_archived': bool(ch.get('is_archived')),
            'integrations': by_channel.get(ch.get('id'), []),
        })
    bot = slack_helpers.auth_test() or {}
    return {
        'channels': rows,
        'bot_user_id': bot.get('user_id'),
        'team': bot.get('team'),
    }


@router.get('/slack/integrations')
def list_slack_integrations(
    event_type: str | None = None,
    slack_integration_store=Depends(get_slack_integration_store),
) -> dict[str, Any]:
    items = slack_integration_store.list_integrations(event_type=event_type)
    return {'items': items, 'total': len(items)}


@router.post('/slack/integrations', status_code=status.HTTP_201_CREATED)
def upsert_slack_integration(
    payload: SlackIntegrationCreate = Body(...),
    slack_integration_store=Depends(get_slack_integration_store),
) -> dict[str, Any]:
    return slack_integration_store.upsert_integration(
        slack_channel_id=payload.slack_channel_id,
        slack_channel_name=payload.slack_channel_name,
        event_type=payload.event_type.strip(),
    )


@router.patch('/slack/integrations/{integration_id}')
def toggle_slack_integration(
    integration_id: int,
    payload: SlackIntegrationToggle = Body(...),
    slack_integration_store=Depends(get_slack_integration_store),
) -> dict[str, Any]:
    return slack_integration_store.set_enabled(integration_id, payload.enabled)


@router.delete('/slack/integrations/{integration_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_slack_integration(
    integration_id: int,
    slack_integration_store=Depends(get_slack_integration_store),
) -> None:
    slack_integration_store.delete_integration(integration_id)


@router.post('/slack/channels/{channel_id}/invite')
def invite_bot_to_channel(channel_id: str) -> dict[str, Any]:
    """Invite the bot itself into ``channel_id`` so it can post there.
    Returns the raw Slack response so the front-end can surface useful
    error codes (already_in_channel, channel_not_found, etc.)."""
    bot = slack_helpers.auth_test() or {}
    bot_user_id = bot.get('user_id')
    if not bot_user_id:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail='Could not resolve bot user id from Slack auth.test — check SLACK_BOT_TOKEN.',
        )
    result = slack_helpers.invite_user_to_channel(channel_id, bot_user_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail='Slack invite call failed.')
    return result
