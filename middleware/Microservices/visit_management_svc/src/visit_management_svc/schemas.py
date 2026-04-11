from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel


class VisitCreate(BaseModel):
    member_id: int
    appointment_id: int | None = None
    staff_id: int | None = None
    visit_date: date | None = None
    status: str = 'scheduled'
    started_at: datetime | None = None
    completed_at: datetime | None = None
    notes_summary: str | None = None


class VisitResponse(BaseModel):
    id: int
    member_id: int
    appointment_id: int | None = None
    staff_id: int | None = None
    visit_date: date | None = None
    status: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    notes_summary: str | None = None
    created_at: datetime | None = None


class VisitNoteCreate(BaseModel):
    note: str
    author_name: str | None = None


class VisitDecisionCreate(BaseModel):
    decision: str
    owner_name: str | None = None


class VisitActionItemCreate(BaseModel):
    description: str
    due_date: date | None = None
    status: str = 'open'


class VisitDocumentCreate(BaseModel):
    title: str
    doc_type: str
    mime_type: str | None = None
    file_path: str | None = None
    summary: str | None = None


class VisitDocumentResponse(BaseModel):
    id: int
    visit_id: int
    title: str
    doc_type: str
    mime_type: str | None = None
    file_path: str | None = None
    summary: str | None = None
    created_at: datetime | None = None


class VisitNoteResponse(BaseModel):
    id: int
    visit_id: int
    note: str
    author_name: str | None = None
    created_at: datetime | None = None


class VisitDecisionResponse(BaseModel):
    id: int
    visit_id: int
    decision: str
    owner_name: str | None = None
    created_at: datetime | None = None


class VisitActionItemResponse(BaseModel):
    id: int
    visit_id: int
    description: str
    due_date: date | None = None
    status: str
    created_at: datetime | None = None
