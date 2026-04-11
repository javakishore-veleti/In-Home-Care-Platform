"""Block Kit renderers for appointment-related Slack messages.

These live in slack_svc — not in shared/ — because Slack rendering is a
slack_svc concern. The shapes follow Slack's Block Kit reference:
https://api.slack.com/block-kit
"""
from __future__ import annotations

from typing import Any

CLAIM_ACTION_ID = 'claim_appointment'


def _coerce_date(value: Any) -> str:
    if value is None:
        return '—'
    if hasattr(value, 'isoformat'):
        return value.isoformat()
    return str(value)


def appointment_request(appointment: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    """Original Block Kit message with a Claim button."""
    appt_id = appointment.get('id')
    service_type = appointment.get('service_type') or 'In-home visit'
    service_area = appointment.get('service_area') or '—'
    requested_date = _coerce_date(appointment.get('requested_date'))
    requested_time_slot = appointment.get('requested_time_slot') or '—'
    member_id = appointment.get('member_id')
    reason = appointment.get('reason') or '—'

    fallback = f'New appointment request #{appt_id}: {service_type} on {requested_date} ({requested_time_slot})'
    blocks: list[dict[str, Any]] = [
        {
            'type': 'header',
            'text': {'type': 'plain_text', 'text': f'New appointment request #{appt_id}'},
        },
        {
            'type': 'section',
            'fields': [
                {'type': 'mrkdwn', 'text': f'*Service:*\n{service_type}'},
                {'type': 'mrkdwn', 'text': f'*Area:*\n{service_area}'},
                {'type': 'mrkdwn', 'text': f'*Date:*\n{requested_date}'},
                {'type': 'mrkdwn', 'text': f'*Time slot:*\n{requested_time_slot}'},
                {'type': 'mrkdwn', 'text': f'*Member ID:*\n{member_id}'},
                {'type': 'mrkdwn', 'text': f'*Reason:*\n{reason}'},
            ],
        },
        {
            'type': 'actions',
            'block_id': f'appointment_claim_{appt_id}',
            'elements': [
                {
                    'type': 'button',
                    'action_id': CLAIM_ACTION_ID,
                    'style': 'primary',
                    'text': {'type': 'plain_text', 'text': 'Claim'},
                    'value': str(appt_id),
                },
            ],
        },
    ]
    return fallback, blocks


def appointment_claimed(appointment: dict[str, Any], slack_user_id: str) -> tuple[str, list[dict[str, Any]]]:
    """Replacement message after a successful claim — button is gone."""
    appt_id = appointment.get('id')
    service_type = appointment.get('service_type') or 'In-home visit'
    requested_date = _coerce_date(appointment.get('requested_date'))
    requested_time_slot = appointment.get('requested_time_slot') or '—'

    fallback = f'Appointment #{appt_id} claimed by <@{slack_user_id}>'
    blocks: list[dict[str, Any]] = [
        {
            'type': 'header',
            'text': {'type': 'plain_text', 'text': f'Appointment #{appt_id} — claimed'},
        },
        {
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': (
                    f'*Claimed by:* <@{slack_user_id}>\n'
                    f'*Service:* {service_type}\n'
                    f'*When:* {requested_date} ({requested_time_slot})'
                ),
            },
        },
    ]
    return fallback, blocks


def appointment_unavailable(appointment_id: int, reason: str) -> tuple[str, list[dict[str, Any]]]:
    """Used when the appointment was deleted/cancelled before we could post."""
    fallback = f'Appointment #{appointment_id} is no longer available ({reason})'
    blocks: list[dict[str, Any]] = [
        {
            'type': 'section',
            'text': {'type': 'mrkdwn', 'text': fallback},
        },
    ]
    return fallback, blocks
