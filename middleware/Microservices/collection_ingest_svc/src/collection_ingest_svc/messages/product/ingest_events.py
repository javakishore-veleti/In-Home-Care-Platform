"""Outbound event definitions for the ingest service.

These events could be published to Kafka for downstream consumers
(e.g. the care_admin_portal dashboard refresh).
"""
from __future__ import annotations

from pydantic import BaseModel

from ...common.enums import IngestStatus


class IngestStartedEvent(BaseModel):
    collection_id: int
    collection_name: str
    vector_dbs: list[str]
    requested_by: str


class IngestCompletedEvent(BaseModel):
    collection_id: int
    collection_name: str
    vector_db: str
    status: IngestStatus
    files_processed: int
    files_failed: int
