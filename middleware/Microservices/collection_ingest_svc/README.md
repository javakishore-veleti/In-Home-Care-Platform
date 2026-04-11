# collection_ingest_svc

FastAPI service that manages document collections and orchestrates their
ingestion into vector databases via Apache Airflow.

## Module structure

```
src/collection_ingest_svc/
├── api/            # FastAPI routes + dependency wiring
├── service/        # Business logic (CollectionService, IngestService)
├── dao/            # Postgres CRUD (CollectionDAO, IngestStatusDAO)
├── handler/        # Third-party invocation (AirflowHandler)
├── messages/
│   ├── product/    # Outbound events (IngestStartedEvent, etc.)
│   └── consumer/   # Inbound handlers (StatusConsumer)
├── util/           # Helpers (file discovery, vector DB config reader)
├── common/         # Models, enums, exceptions
└── main.py         # create_app() factory
```

## Flow

1. Admin portal creates a collection (POST /api/collections).
2. Admin portal triggers ingest (POST /api/ingest/start).
3. IngestService reads system-vector-dbs.json for enabled DBs.
4. For each enabled DB, IngestService triggers the Airflow DAG.
5. Airflow reads files from the collection path, embeds, upserts to
   the vector DB.
6. Airflow calls POST /api/ingest/status to report completion.
7. IngestStatusDAO updates the Postgres row; admin portal polls
   GET /api/ingest/jobs/{collection_id} for status.

**Tech:** FastAPI, psycopg (Postgres), Apache Airflow REST API, Pytest.
