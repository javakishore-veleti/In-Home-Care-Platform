from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from shared.events import APPOINTMENT_BOOKED, APPOINTMENT_EVENTS_TOPIC, build_appointment_event
from shared.kafka import publish

from .schemas import (
    AppointmentClaimRequest,
    AppointmentClaimResponse,
    AppointmentCreate,
    AppointmentListResponse,
    AppointmentResponse,
    AppointmentSlackMessageUpdate,
    AppointmentUpdate,
)
from .store import AppointmentStore

log = logging.getLogger(__name__)

router = APIRouter(tags=['appointments'])
_store = AppointmentStore()


def get_store() -> AppointmentStore:
    return _store


async def _emit_appointment_booked(appointment: dict) -> None:
    """Best-effort Kafka produce — never block create on broker failure."""
    try:
        event = build_appointment_event(APPOINTMENT_BOOKED, appointment['id'])
        await publish(APPOINTMENT_EVENTS_TOPIC, key=str(appointment['id']), value=event)
    except Exception as exc:  # pragma: no cover - never break create on Kafka failure
        log.warning('appointment.kafka_publish_failed', extra={'error': str(exc), 'appointment_id': appointment.get('id')})


@router.post('/appointments', response_model=AppointmentResponse, status_code=201)
async def create_appointment(payload: AppointmentCreate, store: AppointmentStore = Depends(get_store)) -> AppointmentResponse:
    appointment = store.create_appointment(payload)
    await _emit_appointment_booked(appointment)
    return AppointmentResponse(**appointment)


@router.get('/appointments', response_model=AppointmentListResponse)
def list_appointments(
    member_id: int,
    query: str | None = None,
    service_type: str | None = None,
    page: int = 1,
    page_size: int = 10,
    store: AppointmentStore = Depends(get_store),
) -> AppointmentListResponse:
    data = store.list_appointments(member_id=member_id, query=query, service_type=service_type, page=page, page_size=page_size)
    data['items'] = [AppointmentResponse(**row) for row in data['items']]
    return AppointmentListResponse(**data)


@router.get('/appointments/all', response_model=AppointmentListResponse)
def list_all_appointments(
    query: str | None = None,
    status_filter: str | None = None,
    page: int = 1,
    page_size: int = 20,
    store: AppointmentStore = Depends(get_store),
) -> AppointmentListResponse:
    """Cross-member listing for admin/support — never gated by member_id."""
    data = store.list_all_appointments(query=query, status_filter=status_filter, page=page, page_size=page_size)
    data['items'] = [AppointmentResponse(**row) for row in data['items']]
    return AppointmentListResponse(**data)


@router.get('/appointments/{appointment_id}', response_model=AppointmentResponse)
def get_appointment(appointment_id: int, store: AppointmentStore = Depends(get_store)) -> AppointmentResponse:
    return AppointmentResponse(**store.get_appointment(appointment_id))


@router.patch('/appointments/{appointment_id}', response_model=AppointmentResponse)
def update_appointment(appointment_id: int, payload: AppointmentUpdate, store: AppointmentStore = Depends(get_store)) -> AppointmentResponse:
    return AppointmentResponse(**store.update_appointment(appointment_id, payload))


@router.post('/appointments/{appointment_id}/cancel', response_model=AppointmentResponse)
def cancel_appointment(appointment_id: int, store: AppointmentStore = Depends(get_store)) -> AppointmentResponse:
    return AppointmentResponse(**store.cancel_appointment(appointment_id))


@router.patch('/appointments/{appointment_id}/slack-message', response_model=AppointmentResponse)
def attach_slack_message(
    appointment_id: int,
    payload: AppointmentSlackMessageUpdate,
    store: AppointmentStore = Depends(get_store),
) -> AppointmentResponse:
    """Record a successful chat.postMessage for one channel.

    Called by slack_svc after every successful post in the fan-out
    loop. Idempotent per (appointment_id, slack_channel_id) thanks to
    the UNIQUE constraint on appointment_slack_posts.
    """
    store.get_appointment(appointment_id)  # 404 if missing
    return AppointmentResponse(
        **store.attach_slack_message(appointment_id, payload.slack_channel_id, payload.slack_message_ts)
    )


@router.get('/appointments/{appointment_id}/slack-posts')
def list_slack_posts(
    appointment_id: int,
    store: AppointmentStore = Depends(get_store),
) -> dict[str, list[dict]]:
    """Return every channel this appointment has been posted to.

    slack_svc consults this before each post in its fan-out loop to
    avoid double-posting on a Kafka redelivery.
    """
    store.get_appointment(appointment_id)  # 404 if missing
    return {'items': store.list_slack_posts(appointment_id)}


@router.post('/appointments/{appointment_id}/claim', response_model=AppointmentClaimResponse)
def claim_appointment(
    appointment_id: int,
    payload: AppointmentClaimRequest,
    store: AppointmentStore = Depends(get_store),
) -> AppointmentClaimResponse:
    """Record a Slack-originated claim against the appointment.

    Called by slack_svc when a user clicks the Claim button. The endpoint is
    idempotent: if a claim already exists, returns the existing claim with
    `already_claimed=True` so the caller can render the right Slack response.
    """
    if payload.appointment_id != appointment_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='appointment_id mismatch.')
    result = store.claim_appointment_via_slack(
        appointment_id,
        slack_user_id=payload.slack_user_id,
        slack_user_name=payload.slack_user_name,
        slack_team_id=payload.slack_team_id,
        slack_channel_id=payload.slack_channel_id,
        slack_message_ts=payload.slack_message_ts,
    )
    return AppointmentClaimResponse(
        appointment=AppointmentResponse(**result['appointment']),
        claim=result['claim'],
        already_claimed=result['already_claimed'],
    )
