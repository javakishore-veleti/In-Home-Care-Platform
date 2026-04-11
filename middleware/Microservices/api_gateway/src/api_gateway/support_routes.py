"""Read-only cross-member endpoints for the customer_support_app.

Gated by ``require_roles({'support', 'admin'})`` so an admin can also use
this surface during incident response. Cases are persisted in
``member_schema.support_cases`` (lives in member_svc until/unless a
dedicated support_svc is split out).
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, status
from pydantic import BaseModel, Field

from .dependencies import (
    SessionContext,
    get_appointment_client,
    get_member_store,
    get_support_case_store,
    get_visit_store,
    require_roles,
)

ALLOWED_PRIORITIES = {'low', 'medium', 'high', 'urgent'}

router = APIRouter(
    prefix='/api/support',
    tags=['support'],
    dependencies=[Depends(require_roles({'support', 'admin'}))],
)


class SupportCaseCreate(BaseModel):
    member_id: int
    subject: str = Field(min_length=1, max_length=255)
    description: str | None = None
    priority: str = 'medium'


@router.get('/cases')
def list_cases(
    member_id: int | None = None,
    status_filter: str | None = None,
    page: int = 1,
    page_size: int = 20,
    support_case_store=Depends(get_support_case_store),
) -> dict[str, Any]:
    return support_case_store.list_cases(
        member_id=member_id,
        status_filter=status_filter,
        page=page,
        page_size=page_size,
    )


@router.post('/cases', status_code=status.HTTP_201_CREATED)
def create_case(
    payload: SupportCaseCreate = Body(...),
    session: SessionContext = Depends(require_roles({'support', 'admin'})),
    support_case_store=Depends(get_support_case_store),
    member_store=Depends(get_member_store),
) -> dict[str, Any]:
    """Open a new support case.

    The acting support user is recorded as ``created_by_user_id`` so we
    have an audit trail without needing the front-end to send it.
    """
    priority = (payload.priority or 'medium').lower()
    if priority not in ALLOWED_PRIORITIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'priority must be one of {sorted(ALLOWED_PRIORITIES)}',
        )
    # Surface a clean 404 if the member doesn't exist instead of a FK violation.
    member_store.get_member(payload.member_id)
    return support_case_store.create_case(
        member_id=payload.member_id,
        subject=payload.subject.strip(),
        description=(payload.description or '').strip() or None,
        priority=priority,
        created_by_user_id=session.user.get('id'),
    )


@router.get('/members')
def search_members(
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


@router.get('/cases/{case_id}')
def get_case(case_id: int, support_case_store=Depends(get_support_case_store)) -> dict[str, Any]:
    return support_case_store.get_case(case_id)
