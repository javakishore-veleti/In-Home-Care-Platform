"""Orchestrates the ingest flow: admin portal -> this service -> Airflow -> vector DBs -> callback."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from ..common.enums import IngestStatus
from ..common.models import IngestJobRecord, IngestRequest, IngestStatusUpdate
from ..dao.collection_dao import CollectionDAO
from ..dao.ingest_status_dao import IngestStatusDAO
from ..handler.airflow_handler import AirflowHandler
from ..util.file_utils import count_files
from ..util.vector_db_config import get_enabled_vector_dbs

DAG_ID = "collection_ingest_dag"


class IngestService:
    def __init__(
        self,
        collection_dao: CollectionDAO,
        ingest_dao: IngestStatusDAO,
        airflow: AirflowHandler,
        vector_db_config_path: str | None = None,
    ) -> None:
        self._collections = collection_dao
        self._ingest = ingest_dao
        self._airflow = airflow
        self._config_path = vector_db_config_path

    def start_ingest(self, request: IngestRequest) -> list[IngestJobRecord]:
        """Kick off ingest for one collection into all enabled vector DBs.

        For each enabled vector DB:
          1. Create an IngestJobRecord (status=PENDING).
          2. Trigger the Airflow DAG with the collection path + vector DB name.
          3. Update the job record with the DAG run ID (status=IN_PROGRESS).

        The Airflow DAG calls back to /api/ingest/status when done.
        """
        collection = self._collections.get_by_id(request.collection_id)
        target_dbs = request.target_vector_dbs or get_enabled_vector_dbs(self._config_path)
        total_files = count_files(collection.base_path)

        jobs: list[IngestJobRecord] = []
        for db_name in target_dbs:
            job = IngestJobRecord(
                collection_id=collection.id,
                collection_name=collection.name,
                vector_db=db_name,
                status=IngestStatus.PENDING,
                files_total=total_files,
                requested_by=request.requested_by,
            )
            job = self._ingest.create_job(job)

            run_id = f"{collection.name}-{db_name}-{uuid.uuid4().hex[:8]}"
            dag_run_id = self._airflow.trigger_dag(
                dag_id=DAG_ID,
                conf={
                    "collection_id": collection.id,
                    "collection_name": collection.name,
                    "base_path": collection.base_path,
                    "vector_db": db_name,
                    "callback_url": "/api/ingest/status",
                },
                run_id=run_id,
            )
            job.airflow_dag_run_id = dag_run_id
            job.status = IngestStatus.IN_PROGRESS
            jobs.append(job)

        return jobs

    def handle_status_callback(self, update: IngestStatusUpdate) -> None:
        """Called by Airflow when a vector DB ingest job completes or fails."""
        self._ingest.update_status(update)

    def get_jobs(self, collection_id: int) -> list[IngestJobRecord]:
        return self._ingest.get_jobs_for_collection(collection_id)
