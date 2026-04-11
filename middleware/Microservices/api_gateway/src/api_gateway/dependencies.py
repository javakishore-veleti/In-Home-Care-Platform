from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from appointment_svc.store import AppointmentStore
from auth_svc.store import AuthStore
from member_svc.schemas import MemberCreate
from member_svc.store import MemberStore
from visit_management_svc.store import VisitStore

from .chat_store import ChatStore


auth_store = AuthStore()
member_store = MemberStore()
appointment_store = AppointmentStore()
visit_store = VisitStore()
chat_store = ChatStore()


@dataclass
class SessionContext:
    token: str
    user: dict
    member: dict


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
    token = _require_bearer_token(authorization)
    user = auth_store.get_current_user(token)
    member = ensure_member_for_user(user)
    return SessionContext(token=token, user=user, member=member)


def get_auth_store() -> AuthStore:
    return auth_store


def get_member_store() -> MemberStore:
    return member_store


def get_appointment_store() -> AppointmentStore:
    return appointment_store


def get_visit_store() -> VisitStore:
    return visit_store


def get_chat_store() -> ChatStore:
    return chat_store


CurrentSession = Annotated[SessionContext, Depends(get_session_context)]
