"""HTTP client that the api_gateway uses to talk to appointment_svc.

Why this exists
---------------
The gateway used to call ``AppointmentStore`` directly via Python imports.
That coupled the two services to the same process and bypassed
``appointment_svc``'s Kafka publish on create. By going through HTTP every
appointment CRUD path — member portal today, admin/field portals tomorrow —
gets the same validation, the same Kafka events, and the same auditability.

The class deliberately mirrors the previous ``AppointmentStore`` method
surface (``create_appointment``, ``get_appointment``, ``list_appointments``,
``update_appointment``, ``cancel_appointment``) so existing call sites in
``member_routes.py`` swap with a one-line dependency change instead of being
rewritten. Each method returns a plain ``dict``, matching the store's old
contract — pydantic conversion happens at the route boundary.
"""
from __future__ import annotations

import logging
import os
from typing import Any

import httpx
from fastapi import HTTPException, status

from appointment_svc.schemas import AppointmentCreate, AppointmentUpdate

log = logging.getLogger(__name__)

APPOINTMENT_SVC_URL = os.getenv('APPOINTMENT_SVC_URL', 'http://127.0.0.1:8004')
HTTP_TIMEOUT = float(os.getenv('APPOINTMENT_SVC_TIMEOUT_SECONDS', '5'))


def _raise_for(resp: httpx.Response) -> None:
    if resp.status_code == 404:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Appointment not found.')
    if resp.is_error:
        # Surface upstream error body so the caller (and the user) can see why.
        try:
            detail = resp.json().get('detail') or resp.text
        except ValueError:
            detail = resp.text
        raise HTTPException(status_code=resp.status_code, detail=detail)


class AppointmentClient:
    """Synchronous HTTP wrapper around appointment_svc.

    A single shared ``httpx.Client`` is reused across requests for connection
    pooling. FastAPI sync endpoints run in the threadpool, so blocking I/O on
    a sync client does not stall the event loop.
    """

    def __init__(self, base_url: str | None = None, timeout: float | None = None) -> None:
        self._client = httpx.Client(
            base_url=base_url or APPOINTMENT_SVC_URL,
            timeout=timeout or HTTP_TIMEOUT,
        )

    def close(self) -> None:
        try:
            self._client.close()
        except Exception:  # pragma: no cover
            pass

    def create_appointment(self, payload: AppointmentCreate) -> dict[str, Any]:
        resp = self._client.post('/appointments', json=payload.model_dump(mode='json'))
        _raise_for(resp)
        return resp.json()

    def get_appointment(self, appointment_id: int) -> dict[str, Any]:
        resp = self._client.get(f'/appointments/{appointment_id}')
        _raise_for(resp)
        return resp.json()

    def list_appointments(
        self,
        *,
        member_id: int,
        query: str | None = None,
        service_type: str | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {'member_id': member_id, 'page': page, 'page_size': page_size}
        if query:
            params['query'] = query
        if service_type:
            params['service_type'] = service_type
        resp = self._client.get('/appointments', params=params)
        _raise_for(resp)
        return resp.json()

    def update_appointment(self, appointment_id: int, payload: AppointmentUpdate) -> dict[str, Any]:
        resp = self._client.patch(
            f'/appointments/{appointment_id}',
            json=payload.model_dump(mode='json', exclude_unset=True),
        )
        _raise_for(resp)
        return resp.json()

    def cancel_appointment(self, appointment_id: int) -> dict[str, Any]:
        resp = self._client.post(f'/appointments/{appointment_id}/cancel')
        _raise_for(resp)
        return resp.json()
