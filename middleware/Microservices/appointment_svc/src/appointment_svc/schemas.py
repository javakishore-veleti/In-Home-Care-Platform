from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class AppointmentCreate(BaseModel):
    member_id: int
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


class AppointmentUpdate(BaseModel):
    service_type: str | None = None
    service_area: str | None = None
    requested_date: date | None = None
    requested_time_slot: str | None = None
    preferred_hour: str | None = None
    preferred_minute: str | None = None
    scheduled_start: datetime | None = None
    scheduled_end: datetime | None = None
    reason: str | None = None
    notes: str | None = None
    status: str | None = None


class AppointmentResponse(BaseModel):
    id: int
    member_id: int
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
    status: str
    assigned_staff_id: int | None = None
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    cancelled_at: datetime | None = None
    slack_channel_id: str | None = None
    slack_message_ts: str | None = None
    claimed_by_slack_user_id: str | None = None
    claimed_by_slack_user_name: str | None = None
    claimed_at: datetime | None = None


class AppointmentListResponse(BaseModel):
    items: list[AppointmentResponse]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total: int = Field(ge=0)
    total_pages: int = Field(ge=1)


class AppointmentSlackMessageUpdate(BaseModel):
    slack_channel_id: str
    slack_message_ts: str


class AppointmentClaimRequest(BaseModel):
    appointment_id: int
    slack_user_id: str
    slack_user_name: str | None = None
    slack_team_id: str | None = None
    slack_channel_id: str | None = None
    slack_message_ts: str | None = None


class AppointmentClaimResponse(BaseModel):
    appointment: AppointmentResponse
    claim: dict[str, Any]
    already_claimed: bool
