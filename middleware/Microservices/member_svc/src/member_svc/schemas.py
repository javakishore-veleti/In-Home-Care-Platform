from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class MemberCreate(BaseModel):
    user_id: int
    tenant_id: str = 'member-portal'
    first_name: str = ''
    last_name: str = ''
    email: str
    phone: str | None = None
    dob: date | None = None
    insurance_id: str | None = None
    preferences: dict[str, Any] = Field(default_factory=dict)


class MemberUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    dob: date | None = None
    insurance_id: str | None = None
    preferences: dict[str, Any] | None = None


class MemberProfile(BaseModel):
    id: int
    user_id: int
    tenant_id: str
    first_name: str = ''
    last_name: str = ''
    email: str
    phone: str | None = None
    dob: date | None = None
    insurance_id: str | None = None
    preferences: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class AddressCreate(BaseModel):
    label: str = 'Home'
    line1: str
    line2: str | None = None
    city: str
    state: str
    postal_code: str
    instructions: str | None = None
    is_default: bool = False


class AddressUpdate(BaseModel):
    label: str | None = None
    line1: str | None = None
    line2: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    instructions: str | None = None
    is_default: bool | None = None


class AddressResponse(BaseModel):
    id: int
    member_id: int
    label: str
    line1: str
    line2: str | None = None
    city: str
    state: str
    postal_code: str
    instructions: str | None = None
    is_default: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None
