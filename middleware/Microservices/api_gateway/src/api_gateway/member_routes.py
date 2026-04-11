from __future__ import annotations

from datetime import date, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from appointment_svc.schemas import AppointmentListResponse, AppointmentResponse, AppointmentUpdate
from member_svc.schemas import AddressCreate, AddressListResponse, AddressResponse, AddressUpdate, MemberProfile, MemberUpdate
from visit_management_svc.schemas import (
    VisitActionItemResponse,
    VisitDecisionResponse,
    VisitDocumentResponse,
    VisitNoteResponse,
    VisitResponse,
)

from .dependencies import (
    CurrentSession,
    get_appointment_client,
    get_chat_store,
    get_member_store,
    get_visit_store,
)

router = APIRouter(prefix='/api/member', tags=['member'])


class MemberAppointmentCreate(BaseModel):
    address_id: int
    service_type: str
    service_area: str | None = None
    requested_date: date
    requested_time_slot: str
    preferred_hour: str | None = None
    preferred_minute: str | None = None
    scheduled_start: datetime | None = None
    scheduled_end: datetime | None = None
    reason: str | None = None
    notes: str | None = None


class ChatMessageCreate(BaseModel):
    message: str


class ChatMessageResponse(BaseModel):
    id: int
    member_id: int
    role: str
    message: str
    created_at: datetime | None = None


class ChatThreadResponse(BaseModel):
    messages: list[ChatMessageResponse]


@router.get('/profile', response_model=MemberProfile)
def get_profile(session: CurrentSession) -> MemberProfile:
    return MemberProfile(**session.member)


@router.patch('/profile', response_model=MemberProfile)
def update_profile(payload: MemberUpdate, session: CurrentSession, member_store=Depends(get_member_store)) -> MemberProfile:
    return MemberProfile(**member_store.update_member(session.member['id'], payload))


@router.get('/addresses', response_model=list[AddressResponse])
def list_addresses(session: CurrentSession, member_store=Depends(get_member_store)) -> list[AddressResponse]:
    return [AddressResponse(**row) for row in member_store.list_addresses(session.member['id'])]


@router.get('/address-directory', response_model=AddressListResponse)
def search_addresses(
    session: CurrentSession,
    query: str | None = None,
    page: int = 1,
    page_size: int = 10,
    member_store=Depends(get_member_store),
) -> AddressListResponse:
    data = member_store.search_addresses(member_id=session.member['id'], query=query, page=page, page_size=page_size)
    data['items'] = [AddressResponse(**row) for row in data['items']]
    return AddressListResponse(**data)


@router.post('/addresses', response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
def create_address(payload: AddressCreate, session: CurrentSession, member_store=Depends(get_member_store)) -> AddressResponse:
    return AddressResponse(**member_store.create_address(session.member['id'], payload))


@router.patch('/addresses/{address_id}', response_model=AddressResponse)
def update_address(address_id: int, payload: AddressUpdate, session: CurrentSession, member_store=Depends(get_member_store)) -> AddressResponse:
    return AddressResponse(**member_store.update_address(session.member['id'], address_id, payload))


@router.delete('/addresses/{address_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_address(address_id: int, session: CurrentSession, member_store=Depends(get_member_store)) -> None:
    member_store.delete_address(session.member['id'], address_id)


@router.patch('/addresses/{address_id}/default', response_model=AddressResponse)
def set_default_address(address_id: int, session: CurrentSession, member_store=Depends(get_member_store)) -> AddressResponse:
    return AddressResponse(**member_store.set_default_address(session.member['id'], address_id))


@router.post('/appointments', response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
def create_appointment(
    payload: MemberAppointmentCreate,
    session: CurrentSession,
    appointment_client=Depends(get_appointment_client),
    member_store=Depends(get_member_store),
) -> AppointmentResponse:
    addresses = member_store.list_addresses(session.member['id'])
    if not any(address['id'] == payload.address_id for address in addresses):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Appointment must use one of your saved addresses.')
    from appointment_svc.schemas import AppointmentCreate

    appointment = appointment_client.create_appointment(
        AppointmentCreate(member_id=session.member['id'], **payload.model_dump()),
    )
    return AppointmentResponse(**appointment)


@router.get('/appointments', response_model=AppointmentListResponse)
def list_appointments(
    session: CurrentSession,
    query: str | None = None,
    service_type: str | None = None,
    page: int = 1,
    page_size: int = 10,
    appointment_client=Depends(get_appointment_client),
) -> AppointmentListResponse:
    data = appointment_client.list_appointments(
        member_id=session.member['id'],
        query=query,
        service_type=service_type,
        page=page,
        page_size=page_size,
    )
    data['items'] = [AppointmentResponse(**row) for row in data['items']]
    return AppointmentListResponse(**data)


@router.get('/appointments/{appointment_id}', response_model=AppointmentResponse)
def get_appointment(appointment_id: int, session: CurrentSession, appointment_client=Depends(get_appointment_client)) -> AppointmentResponse:
    appointment = appointment_client.get_appointment(appointment_id)
    _ensure_appointment_owner(appointment, session.member['id'])
    return AppointmentResponse(**appointment)


@router.patch('/appointments/{appointment_id}', response_model=AppointmentResponse)
def update_appointment(
    appointment_id: int,
    payload: AppointmentUpdate,
    session: CurrentSession,
    appointment_client=Depends(get_appointment_client),
) -> AppointmentResponse:
    appointment = appointment_client.get_appointment(appointment_id)
    _ensure_appointment_owner(appointment, session.member['id'])
    return AppointmentResponse(**appointment_client.update_appointment(appointment_id, payload))


@router.post('/appointments/{appointment_id}/cancel', response_model=AppointmentResponse)
def cancel_appointment(
    appointment_id: int,
    session: CurrentSession,
    appointment_client=Depends(get_appointment_client),
) -> AppointmentResponse:
    appointment = appointment_client.get_appointment(appointment_id)
    _ensure_appointment_owner(appointment, session.member['id'])
    return AppointmentResponse(**appointment_client.cancel_appointment(appointment_id))


@router.get('/appointments/{appointment_id}/visits', response_model=list[VisitResponse])
def list_visits(
    appointment_id: int,
    session: CurrentSession,
    appointment_client=Depends(get_appointment_client),
    visit_store=Depends(get_visit_store),
) -> list[VisitResponse]:
    appointment = appointment_client.get_appointment(appointment_id)
    _ensure_appointment_owner(appointment, session.member['id'])
    return [VisitResponse(**row) for row in visit_store.list_visits_for_appointment(appointment_id)]


@router.get('/visits/{visit_id}', response_model=VisitResponse)
def get_visit(visit_id: int, session: CurrentSession, visit_store=Depends(get_visit_store)) -> VisitResponse:
    visit = visit_store.get_visit(visit_id)
    _ensure_visit_owner(visit, session.member['id'])
    return VisitResponse(**visit)


@router.get('/visits/{visit_id}/documents', response_model=list[VisitDocumentResponse])
def list_visit_documents(visit_id: int, session: CurrentSession, visit_store=Depends(get_visit_store)) -> list[VisitDocumentResponse]:
    visit = visit_store.get_visit(visit_id)
    _ensure_visit_owner(visit, session.member['id'])
    return [VisitDocumentResponse(**row) for row in visit_store.list_documents(visit_id)]


@router.get('/visits/{visit_id}/notes', response_model=list[VisitNoteResponse])
def list_visit_notes(visit_id: int, session: CurrentSession, visit_store=Depends(get_visit_store)) -> list[VisitNoteResponse]:
    visit = visit_store.get_visit(visit_id)
    _ensure_visit_owner(visit, session.member['id'])
    return [VisitNoteResponse(**row) for row in visit_store.list_notes(visit_id)]


@router.get('/visits/{visit_id}/decisions', response_model=list[VisitDecisionResponse])
def list_visit_decisions(visit_id: int, session: CurrentSession, visit_store=Depends(get_visit_store)) -> list[VisitDecisionResponse]:
    visit = visit_store.get_visit(visit_id)
    _ensure_visit_owner(visit, session.member['id'])
    return [VisitDecisionResponse(**row) for row in visit_store.list_decisions(visit_id)]


@router.get('/visits/{visit_id}/action-items', response_model=list[VisitActionItemResponse])
def list_visit_action_items(visit_id: int, session: CurrentSession, visit_store=Depends(get_visit_store)) -> list[VisitActionItemResponse]:
    visit = visit_store.get_visit(visit_id)
    _ensure_visit_owner(visit, session.member['id'])
    return [VisitActionItemResponse(**row) for row in visit_store.list_action_items(visit_id)]


@router.get('/chat/messages', response_model=ChatThreadResponse)
def list_chat_messages(session: CurrentSession, chat_store=Depends(get_chat_store)) -> ChatThreadResponse:
    messages = [ChatMessageResponse(**row) for row in chat_store.list_messages(session.member['id'])]
    return ChatThreadResponse(messages=messages)


@router.post('/chat/messages', response_model=ChatThreadResponse)
def send_chat_message(
    payload: ChatMessageCreate,
    session: CurrentSession,
    chat_store=Depends(get_chat_store),
    appointment_client=Depends(get_appointment_client),
) -> ChatThreadResponse:
    chat_store.add_message(session.member['id'], 'user', payload.message)
    reply = _generate_chat_reply(payload.message, session.member, appointment_client)
    chat_store.add_message(session.member['id'], 'assistant', reply)
    messages = [ChatMessageResponse(**row) for row in chat_store.list_messages(session.member['id'])]
    return ChatThreadResponse(messages=messages)


def _ensure_appointment_owner(appointment: dict[str, Any], member_id: int) -> None:
    if appointment['member_id'] != member_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Appointment not found.')


def _ensure_visit_owner(visit: dict[str, Any], member_id: int) -> None:
    if visit['member_id'] != member_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Visit not found.')


def _generate_chat_reply(message: str, member: dict[str, Any], appointment_client) -> str:
    lowered = message.lower()
    appointment_snapshot = appointment_client.list_appointments(member_id=member['id'], page=1, page_size=3)
    if 'appointment' in lowered:
        count = appointment_snapshot['total']
        return f"You currently have {count} appointment request(s) on file. I can help you review an upcoming visit, confirm your saved address, or suggest questions for your care team."
    if 'address' in lowered:
        return 'You can manage your saved service addresses from Profile Settings. When booking, choose the address that best matches where the visit should happen.'
    if 'visit' in lowered or 'document' in lowered:
        return 'Visit details include documents, notes, decisions, and action items after your care team records them. Open an appointment to review the latest care updates.'
    first_name = member.get('first_name') or 'there'
    return f'Hi {first_name}, thanks for reaching out. I can help with appointments, address updates, and reviewing visit follow-ups. Ask me about anything in your member portal.'
