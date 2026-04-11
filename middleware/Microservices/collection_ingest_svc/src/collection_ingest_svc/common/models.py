from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .enums import CollectionCategory, FileFormat, IngestStatus


class Collection(BaseModel):
    """A collection defined by admin in the care_admin_portal.
    Backed by a Postgres row managed via collection_dao.
    """
    id: int | None = None
    name: str
    description: str = ""
    base_path: str = Field(
        description="Local path or S3 URI where ingest-pending files live. "
                    "e.g. collections/ingest-pending/policy-docs"
    )
    categories: list[CollectionCategory] = Field(
        default_factory=lambda: list(CollectionCategory),
    )
    created_by: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None


class IngestRequest(BaseModel):
    """Request to ingest a collection into vector DBs."""
    collection_id: int
    collection_name: str
    base_path: str
    target_vector_dbs: list[str] = Field(
        default_factory=list,
        description="Which vector DBs to ingest into. "
                    "Read from system-vector-dbs.json if empty.",
    )
    requested_by: str = ""


class IngestStatusUpdate(BaseModel):
    """Callback from Airflow when ingestion completes."""
    collection_id: int
    collection_name: str
    vector_db: str
    status: IngestStatus
    files_processed: int = 0
    files_failed: int = 0
    error_message: str | None = None
    completed_at: datetime | None = None


class IngestJobRecord(BaseModel):
    """Persistent record of one ingest job (one collection x one vector DB)."""
    id: int | None = None
    collection_id: int
    collection_name: str
    vector_db: str
    status: IngestStatus = IngestStatus.PENDING
    airflow_dag_run_id: str | None = None
    files_total: int = 0
    files_processed: int = 0
    files_failed: int = 0
    error_message: str | None = None
    requested_by: str = ""
    requested_at: datetime | None = None
    completed_at: datetime | None = None
