from __future__ import annotations

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from auth_svc.schemas import AuthResponse, SigninRequest, SignupRequest
from member_svc.schemas import MemberCreate, MemberProfile

from .dependencies import CurrentSession, ensure_member_for_user, get_auth_store, get_member_store

router = APIRouter(prefix='/api/auth', tags=['member-auth'])


class GatewaySignupResponse(BaseModel):
    user: dict
    member: MemberProfile


class GatewaySessionResponse(AuthResponse):
    member: MemberProfile


class GatewayMeResponse(BaseModel):
    user: dict
    member: MemberProfile


@router.post('/signup', response_model=GatewaySignupResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, auth_store=Depends(get_auth_store), member_store=Depends(get_member_store)) -> GatewaySignupResponse:
    user = auth_store.create_user(payload)
    member = member_store.create_member(
        MemberCreate(
            user_id=user['id'],
            email=user['email'],
            first_name=payload.first_name,
            last_name=payload.last_name,
            phone=payload.phone,
        ),
    )
    return GatewaySignupResponse(user=user, member=MemberProfile(**member))


@router.post('/signin', response_model=GatewaySessionResponse)
def signin(payload: SigninRequest, auth_store=Depends(get_auth_store)) -> GatewaySessionResponse:
    session = auth_store.signin(payload)
    member = ensure_member_for_user(session['user'])
    return GatewaySessionResponse(**session, member=MemberProfile(**member))


@router.get('/me', response_model=GatewayMeResponse)
def me(session: CurrentSession) -> GatewayMeResponse:
    return GatewayMeResponse(user=session.user, member=MemberProfile(**session.member))
