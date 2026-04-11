"""Async invocation of Apache Airflow to run the collection ingest DAG.

The admin portal calls IngestService.start_ingest() which calls this
handler to trigger the Airflow DAG via the Airflow REST API. The DAG
does the heavy lifting (read files, embed, upsert to each vector DB)
and calls back to the ingest service's /api/ingest/status endpoint
when done.
"""
from __future__ import annotations

import json
import urllib.request
import urllib.error
from typing import Any

from ..common.exceptions import AirflowInvocationError


class AirflowHandler:
    def __init__(
        self,
        base_url: str = "http://localhost:8082",
        username: str = "airflow",
        password: str = "airflow",
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._auth = (username, password)

    def trigger_dag(
        self,
        dag_id: str,
        conf: dict[str, Any],
        run_id: str | None = None,
    ) -> str:
        """Trigger an Airflow DAG run. Returns the dag_run_id."""
        url = f"{self._base_url}/api/v1/dags/{dag_id}/dagRuns"
        payload: dict[str, Any] = {"conf": conf}
        if run_id:
            payload["dag_run_id"] = run_id

        data = json.dumps(payload).encode("utf-8")
        import base64
        creds = base64.b64encode(
            f"{self._auth[0]}:{self._auth[1]}".encode()
        ).decode()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {creds}",
        }
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode())
                return result.get("dag_run_id", "unknown")
        except urllib.error.HTTPError as e:
            body = e.read().decode() if e.fp else ""
            raise AirflowInvocationError(
                f"Airflow returned {e.code}: {body}"
            ) from e
        except Exception as e:
            raise AirflowInvocationError(f"Failed to invoke Airflow: {e}") from e

    def get_dag_run_status(self, dag_id: str, dag_run_id: str) -> str:
        url = f"{self._base_url}/api/v1/dags/{dag_id}/dagRuns/{dag_run_id}"
        import base64
        creds = base64.b64encode(
            f"{self._auth[0]}:{self._auth[1]}".encode()
        ).decode()
        headers = {"Authorization": f"Basic {creds}"}
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode())
                return result.get("state", "unknown")
        except Exception:
            return "unknown"


class FakeAirflowHandler:
    """In-memory handler for tests."""

    def __init__(self) -> None:
        self.triggered: list[dict[str, Any]] = []
        self._seq = 0

    def trigger_dag(self, dag_id: str, conf: dict[str, Any], run_id: str | None = None) -> str:
        self._seq += 1
        dag_run_id = run_id or f"fake-run-{self._seq}"
        self.triggered.append({"dag_id": dag_id, "conf": conf, "dag_run_id": dag_run_id})
        return dag_run_id

    def get_dag_run_status(self, dag_id: str, dag_run_id: str) -> str:
        return "success"
