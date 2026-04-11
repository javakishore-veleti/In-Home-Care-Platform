"""FastAPI routes for collection management and ingest orchestration."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..common.exceptions import CollectionNotFoundError
from ..common.models import Collection, IngestRequest, IngestStatusUpdate
from ..service.collection_service import CollectionService
from ..service.ingest_service import IngestService

router = APIRouter(prefix="/api", tags=["collections", "ingest"])


# These get overwritten by main.py at startup
_col_svc: CollectionService | None = None
_ingest_svc: IngestService | None = None


def init_routes(col_svc: CollectionService, ingest_svc: IngestService) -> None:
    global _col_svc, _ingest_svc
    _col_svc = col_svc
    _ingest_svc = ingest_svc


# --- Collection CRUD ---

@router.post("/collections")
def create_collection(body: Collection):
    return _col_svc.create(body).model_dump()


@router.get("/collections")
def list_collections():
    return [c.model_dump() for c in _col_svc.list_all()]


@router.get("/collections/{collection_id}")
def get_collection(collection_id: int):
    try:
        return _col_svc.get(collection_id).model_dump()
    except CollectionNotFoundError:
        raise HTTPException(404, "collection not found")


# --- Ingest orchestration ---

@router.post("/ingest/start")
def start_ingest(body: IngestRequest):
    """Admin portal calls this to kick off ingest into all vector DBs."""
    try:
        jobs = _ingest_svc.start_ingest(body)
        return {"jobs": [j.model_dump() for j in jobs]}
    except CollectionNotFoundError:
        raise HTTPException(404, "collection not found")


@router.post("/ingest/status")
def ingest_status_callback(body: IngestStatusUpdate):
    """Airflow calls this when a vector DB ingest job completes."""
    _ingest_svc.handle_status_callback(body)
    return {"ok": True}


@router.get("/ingest/jobs/{collection_id}")
def get_ingest_jobs(collection_id: int):
    jobs = _ingest_svc.get_jobs(collection_id)
    return {"jobs": [j.model_dump() for j in jobs]}
