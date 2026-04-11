from __future__ import annotations

from fastapi import APIRouter, Depends

from .schemas import (
    VisitActionItemCreate,
    VisitActionItemResponse,
    VisitDecisionCreate,
    VisitDecisionResponse,
    VisitDocumentCreate,
    VisitDocumentResponse,
    VisitNoteCreate,
    VisitNoteResponse,
    VisitCreate,
    VisitResponse,
)
from .store import VisitStore

router = APIRouter(tags=['visits'])
_store = VisitStore()


def get_store() -> VisitStore:
    return _store


@router.get('/appointments/{appointment_id}/visits', response_model=list[VisitResponse])
def list_visits_for_appointment(appointment_id: int, store: VisitStore = Depends(get_store)) -> list[VisitResponse]:
    return [VisitResponse(**row) for row in store.list_visits_for_appointment(appointment_id)]


@router.get('/visits/{visit_id}', response_model=VisitResponse)
def get_visit(visit_id: int, store: VisitStore = Depends(get_store)) -> VisitResponse:
    return VisitResponse(**store.get_visit(visit_id))


@router.get('/visits/{visit_id}/documents', response_model=list[VisitDocumentResponse])
def list_documents(visit_id: int, store: VisitStore = Depends(get_store)) -> list[VisitDocumentResponse]:
    return [VisitDocumentResponse(**row) for row in store.list_documents(visit_id)]


@router.get('/visits/{visit_id}/notes', response_model=list[VisitNoteResponse])
def list_notes(visit_id: int, store: VisitStore = Depends(get_store)) -> list[VisitNoteResponse]:
    return [VisitNoteResponse(**row) for row in store.list_notes(visit_id)]


@router.get('/visits/{visit_id}/decisions', response_model=list[VisitDecisionResponse])
def list_decisions(visit_id: int, store: VisitStore = Depends(get_store)) -> list[VisitDecisionResponse]:
    return [VisitDecisionResponse(**row) for row in store.list_decisions(visit_id)]


@router.get('/visits/{visit_id}/action-items', response_model=list[VisitActionItemResponse])
def list_action_items(visit_id: int, store: VisitStore = Depends(get_store)) -> list[VisitActionItemResponse]:
    return [VisitActionItemResponse(**row) for row in store.list_action_items(visit_id)]


@router.post('/visits', response_model=VisitResponse, status_code=201)
def create_visit(payload: VisitCreate, store: VisitStore = Depends(get_store)) -> VisitResponse:
    return VisitResponse(**store.create_visit(payload))


@router.post('/visits/{visit_id}/notes', response_model=VisitNoteResponse, status_code=201)
def create_note(visit_id: int, payload: VisitNoteCreate, store: VisitStore = Depends(get_store)) -> VisitNoteResponse:
    return VisitNoteResponse(**store.create_note(visit_id, payload))


@router.post('/visits/{visit_id}/decisions', response_model=VisitDecisionResponse, status_code=201)
def create_decision(visit_id: int, payload: VisitDecisionCreate, store: VisitStore = Depends(get_store)) -> VisitDecisionResponse:
    return VisitDecisionResponse(**store.create_decision(visit_id, payload))


@router.post('/visits/{visit_id}/action-items', response_model=VisitActionItemResponse, status_code=201)
def create_action_item(visit_id: int, payload: VisitActionItemCreate, store: VisitStore = Depends(get_store)) -> VisitActionItemResponse:
    return VisitActionItemResponse(**store.create_action_item(visit_id, payload))


@router.post('/visits/{visit_id}/documents', response_model=VisitDocumentResponse, status_code=201)
def create_document(visit_id: int, payload: VisitDocumentCreate, store: VisitStore = Depends(get_store)) -> VisitDocumentResponse:
    return VisitDocumentResponse(**store.create_document(visit_id, payload))
