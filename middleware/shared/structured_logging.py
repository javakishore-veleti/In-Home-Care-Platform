"""Structured JSON logging for ELK/Kibana ingestion.

Call configure_structured_logging() in any service's main.py to
switch from plain-text logging to structured JSON that Filebeat/
Logstash can ship to Elasticsearch for Kibana dashboards.

Usage:
    from shared.structured_logging import configure_structured_logging
    configure_structured_logging(service_name='knowledge_agent_svc')
"""
from __future__ import annotations

import logging
import json
import sys
from datetime import datetime, timezone
from typing import Any


class JSONFormatter(logging.Formatter):
    """Emit each log record as a single-line JSON object."""

    def __init__(self, service_name: str = 'unknown') -> None:
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'service': self.service_name,
        }
        if record.exc_info and record.exc_info[1]:
            log_entry['exception'] = self.formatException(record.exc_info)
        # Include any extra fields passed via log.info('msg', extra={...})
        for key in ('appointment_id', 'model_id', 'provider', 'service_type',
                     'input_tokens', 'output_tokens', 'cost_usd', 'latency_ms',
                     'rag_chunks_used', 'collection_slug', 'error', 'status'):
            val = getattr(record, key, None)
            if val is not None:
                log_entry[key] = val
        return json.dumps(log_entry, default=str)


def configure_structured_logging(
    service_name: str = 'unknown',
    level: int = logging.INFO,
) -> None:
    """Replace the root logger's handler with a JSON formatter."""
    root = logging.getLogger()
    root.setLevel(level)
    # Remove existing handlers
    for handler in root.handlers[:]:
        root.removeHandler(handler)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter(service_name=service_name))
    root.addHandler(handler)
    # Keep noisy libraries at WARNING
    logging.getLogger('aiokafka').setLevel(logging.WARNING)
    logging.getLogger('kafka').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
