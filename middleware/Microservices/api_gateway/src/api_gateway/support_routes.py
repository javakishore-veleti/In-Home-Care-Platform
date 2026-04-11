"""Read-only cross-member endpoints for the customer_support_app.

Gated by ``require_roles({'support', 'admin'})`` so an admin can also use
this surface during incident response. Cases are stubbed for now (no
support_cases table yet) — the endpoint returns an empty list with the
right shape so the desktop app's Cases screen renders the empty state
instead of dummy rows.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from .dependencies import (
    get_appointment_client,
    get_member_store,
    get_visit_store,
    require_roles,
)

router = APIRouter(
    prefix='/api/support',
    tags=['support'],
    dependencies=[Depends(require_roles({'support', 'admin'}))],
)


@router.get('/cases')
def list_cases(page: int = 1, page_size: int = 20) -> dict[str, Any]:
    """Stub list — support_cases table not implemented yet.

    Returning the right pagination shape lets the front-end render an empty
    state without special-casing. Replace once the cases domain exists.
    """
    return {
        'items': [],
        'page': max(1, page),
        'page_size': max(1, min(page_size, 100)),
        'total': 0,
        'total_pages': 1,
    }


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
