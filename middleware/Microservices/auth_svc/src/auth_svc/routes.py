from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status

from .schemas import AuthResponse, AuthUser, SigninRequest, SignupRequest, SignupResponse
from .store import AuthStore

router = APIRouter(tags=['auth'])
_store = AuthStore()


def get_store() -> AuthStore:
    return _store


def require_bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith('bearer '):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Missing bearer token.')
    return authorization.split(' ', 1)[1].strip()


@router.post('/auth/signup', response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, store: AuthStore = Depends(get_store)) -> SignupResponse:
    return SignupResponse(user=store.create_user(payload))


@router.post('/auth/signin', response_model=AuthResponse)
def signin(payload: SigninRequest, store: AuthStore = Depends(get_store)) -> AuthResponse:
    return AuthResponse(**store.signin(payload))


@router.get('/auth/me', response_model=AuthUser)
def me(
    authorization: Annotated[str | None, Header()] = None,
    store: AuthStore = Depends(get_store),
) -> AuthUser:
    token = require_bearer_token(authorization)
    return AuthUser(**store.get_current_user(token))
