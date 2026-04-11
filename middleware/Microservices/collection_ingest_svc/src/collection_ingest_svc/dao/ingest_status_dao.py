"""Ingest job status tracking against Postgres."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ..common.enums import IngestStatus
from ..common.models import IngestJobRecord, IngestStatusUpdate


class IngestStatusDAO:
    def __init__(self, pool: Any) -> None:
        self._pool = pool

    def create_job(self, job: IngestJobRecord) -> IngestJobRecord:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO ingest_jobs
                       (collection_id, collection_name, vector_db, status,
                        airflow_dag_run_id, files_total, requested_by, requested_at)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                    (job.collection_id, job.collection_name, job.vector_db,
                     job.status.value, job.airflow_dag_run_id, job.files_total,
                     job.requested_by, datetime.now(tz=timezone.utc)),
                )
                job.id = cur.fetchone()[0]
                conn.commit()
        return job

    def update_status(self, update: IngestStatusUpdate) -> None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """UPDATE ingest_jobs
                       SET status = %s, files_processed = %s, files_failed = %s,
                           error_message = %s, completed_at = %s
                       WHERE collection_id = %s AND vector_db = %s
                       AND status != 'completed'""",
                    (update.status.value, update.files_processed, update.files_failed,
                     update.error_message, update.completed_at or datetime.now(tz=timezone.utc),
                     update.collection_id, update.vector_db),
                )
                conn.commit()

    def get_jobs_for_collection(self, collection_id: int) -> list[IngestJobRecord]:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM ingest_jobs WHERE collection_id = %s ORDER BY requested_at DESC",
                    (collection_id,),
                )
                return [self._row_to_model(r, cur.description) for r in cur.fetchall()]

    def _row_to_model(self, row: tuple, desc: Any) -> IngestJobRecord:
        cols = [d.name for d in desc]
        return IngestJobRecord(**dict(zip(cols, row)))


class FakeIngestStatusDAO:
    """In-memory DAO for tests."""

    def __init__(self) -> None:
        self._store: list[IngestJobRecord] = []
        self._seq = 0

    def create_job(self, job: IngestJobRecord) -> IngestJobRecord:
        self._seq += 1
        job.id = self._seq
        job.requested_at = datetime.now(tz=timezone.utc)
        self._store.append(job)
        return job

    def update_status(self, update: IngestStatusUpdate) -> None:
        for job in self._store:
            if job.collection_id == update.collection_id and job.vector_db == update.vector_db:
                job.status = update.status
                job.files_processed = update.files_processed
                job.files_failed = update.files_failed
                job.error_message = update.error_message
                job.completed_at = update.completed_at or datetime.now(tz=timezone.utc)

    def get_jobs_for_collection(self, collection_id: int) -> list[IngestJobRecord]:
        return [j for j in self._store if j.collection_id == collection_id]
