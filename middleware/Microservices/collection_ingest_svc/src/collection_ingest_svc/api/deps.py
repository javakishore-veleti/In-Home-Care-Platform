"""FastAPI dependency wiring."""
from __future__ import annotations

from ..dao.collection_dao import CollectionDAO, FakeCollectionDAO
from ..dao.ingest_status_dao import IngestStatusDAO, FakeIngestStatusDAO
from ..handler.airflow_handler import AirflowHandler, FakeAirflowHandler
from ..service.collection_service import CollectionService
from ..service.ingest_service import IngestService


def build_services(*, use_fakes: bool = True):
    """Build the service layer. use_fakes=True for local dev / tests."""
    if use_fakes:
        col_dao = FakeCollectionDAO()
        ingest_dao = FakeIngestStatusDAO()
        airflow = FakeAirflowHandler()
    else:
        # Production: inject real Postgres pool + Airflow URL from config
        raise NotImplementedError("Wire real DAOs here")

    col_svc = CollectionService(col_dao)
    ingest_svc = IngestService(col_dao, ingest_dao, airflow)
    return col_svc, ingest_svc
