from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Iterable

from fastapi import Depends, Header, HTTPException, status

from auth_svc.store import AuthStore
from member_svc.schemas import MemberCreate
from member_svc.store import MemberStore
from member_svc.support_case_store import SupportCaseStore
from visit_management_svc.store import VisitStore

from .appointment_client import AppointmentClient
from .chat_store import ChatStore


auth_store = AuthStore()
member_store = MemberStore()
support_case_store = SupportCaseStore()
appointment_client = AppointmentClient()
visit_store = VisitStore()
chat_store = ChatStore()


@dataclass
class SessionContext:
    """Per-request session.

    ``member`` is populated only when ``user.role == 'member'``. Internal-staff
    sessions (admin, support, field_officer, ...) leave it ``None`` so we
    never auto-create a member row for an employee account.
    """
    token: str
    user: dict
    member: dict | None = None


def _require_bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith('bearer '):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Missing bearer token.')
    return authorization.split(' ', 1)[1].strip()


def ensure_member_for_user(user: dict) -> dict:
    member = member_store.get_member_by_user_id(user['id'])
    if member:
        return member
    return member_store.create_member(
        MemberCreate(
            user_id=user['id'],
            email=user['email'],
            first_name='',
            last_name='',
        ),
    )


def get_session_context(
    authorization: Annotated[str | None, Header()] = None,
) -> SessionContext:
    """Decode the JWT and load the user. No member auto-create here."""
    token = _require_bearer_token(authorization)
    user = auth_store.get_current_user(token)
    return SessionContext(token=token, user=user, member=None)


def get_member_session(
    session: SessionContext = Depends(get_session_context),
) -> SessionContext:
    """Member-only entry point: enforces role and lazily attaches the member row."""
    if (session.user.get('role') or 'member') != 'member':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='This endpoint is for member accounts only.')
    member = ensure_member_for_user(session.user)
    return SessionContext(token=session.token, user=session.user, member=member)


def require_roles(allowed_roles: Iterable[str]):
    """FastAPI dependency factory: 403 unless the JWT role is in ``allowed_roles``."""
    allowed = {role for role in allowed_roles}

    def _dep(session: SessionContext = Depends(get_session_context)) -> SessionContext:
        role = session.user.get('role') or 'member'
        if role not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Your role is not allowed to access this resource.')
        return session

    return _dep


def get_auth_store() -> AuthStore:
    return auth_store


def get_member_store() -> MemberStore:
    return member_store


def get_support_case_store() -> SupportCaseStore:
    return support_case_store


def get_appointment_client() -> AppointmentClient:
    return appointment_client


def get_visit_store() -> VisitStore:
    return visit_store


def get_chat_store() -> ChatStore:
    return chat_store


CurrentSession = Annotated[SessionContext, Depends(get_session_context)]
CurrentMemberSession = Annotated[SessionContext, Depends(get_member_session)]
