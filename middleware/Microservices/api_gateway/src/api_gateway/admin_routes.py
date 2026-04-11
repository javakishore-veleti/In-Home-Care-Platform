"""Cross-member endpoints for the care_admin_portal.

All endpoints in this router are gated by ``require_roles({'admin'})`` —
field officers, support, and members get a 403. The router is intentionally
read-mostly: admins inspect the system, mutations should still flow through
the relevant domain service.
"""
from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter, Depends

from .dependencies import (
    get_appointment_client,
    get_auth_store,
    get_member_store,
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
