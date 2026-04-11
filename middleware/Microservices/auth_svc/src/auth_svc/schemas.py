from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class SignupRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)
    first_name: str = ''
    last_name: str = ''
    phone: str | None = None


class SigninRequest(BaseModel):
    email: str
    password: str


class AuthUser(BaseModel):
    id: int
    email: str
    role: str = 'member'
    is_active: bool = True
    created_at: datetime | None = None


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'
    expires_at: datetime
    user: AuthUser


class SignupResponse(BaseModel):
    user: AuthUser
