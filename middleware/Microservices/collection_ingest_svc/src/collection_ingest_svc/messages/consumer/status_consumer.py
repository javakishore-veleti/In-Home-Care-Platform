"""Inbound message handler for Airflow callback events.

In a Kafka-based deployment, Airflow would publish to a topic and this
consumer would drain it. In the current design, Airflow calls back via
HTTP to /api/ingest/status — this module is the handler that the API
route delegates to.
"""
from __future__ import annotations

from ...common.models import IngestStatusUpdate
from ...service.ingest_service import IngestService


class StatusConsumer:
    def __init__(self, ingest_service: IngestService) -> None:
        self._service = ingest_service

    def handle(self, update: IngestStatusUpdate) -> None:
        self._service.handle_status_callback(update)
