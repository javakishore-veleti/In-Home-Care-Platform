"""Shared event names and payload builders for cross-service Kafka traffic.

Keeping topic names and event types in one module avoids string drift between
producers and consumers. Payloads stay intentionally tiny — events carry the
*identifier* and the consumer re-fetches the authoritative record from the
owning service. That way a delete or status change between produce and
consume is observed by the consumer instead of acting on stale data.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

APPOINTMENT_EVENTS_TOPIC = 'appointment.events'
APPOINTMENT_BOOKED = 'appointment.booked'


def build_appointment_event(event_type: str, appointment_id: int) -> dict[str, Any]:
    return {
        'event_type': event_type,
        'appointment_id': int(appointment_id),
        'occurred_at': datetime.now(timezone.utc).isoformat(),
    }
