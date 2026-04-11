from __future__ import annotations

from fastapi import APIRouter, Depends

from .schemas import AppointmentCreate, AppointmentListResponse, AppointmentResponse, AppointmentUpdate
from .store import AppointmentStore

router = APIRouter(tags=['appointments'])
_store = AppointmentStore()


def get_store() -> AppointmentStore:
    return _store


@router.post('/appointments', response_model=AppointmentResponse, status_code=201)
def create_appointment(payload: AppointmentCreate, store: AppointmentStore = Depends(get_store)) -> AppointmentResponse:
    return AppointmentResponse(**store.create_appointment(payload))


@router.get('/appointments', response_model=AppointmentListResponse)
def list_appointments(
    member_id: int,
    query: str | None = None,
    page: int = 1,
    page_size: int = 10,
    store: AppointmentStore = Depends(get_store),
) -> AppointmentListResponse:
    data = store.list_appointments(member_id=member_id, query=query, page=page, page_size=page_size)
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
