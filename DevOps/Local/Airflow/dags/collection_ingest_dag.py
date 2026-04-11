"""Airflow DAG: ingest a document collection into one vector DB.

Triggered by the collection_ingest_svc via the Airflow REST API.
Receives conf with:
    collection_id, collection_name, base_path, vector_db, callback_url

Steps:
    1. discover_files — walk the collection directory
    2. embed_and_upsert — for each file, extract text, embed, upsert
    3. callback — POST status back to the ingest service
"""
from __future__ import annotations

import json
import os
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator


default_args = {
    "owner": "ihcp",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

SUPPORTED_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".odt", ".rtf",
    ".xls", ".xlsx", ".ods",
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff",
    ".csv", ".tsv",
}


def discover_files(**context):
    conf = context["dag_run"].conf or {}
    base_path = conf.get("base_path", "")
    files = []
    if os.path.exists(base_path):
        for root, _, filenames in os.walk(base_path):
            for fn in filenames:
                if Path(fn).suffix.lower() in SUPPORTED_EXTENSIONS:
                    files.append(os.path.join(root, fn))
    context["ti"].xcom_push(key="files", value=files)
    context["ti"].xcom_push(key="total", value=len(files))
    print(f"Discovered {len(files)} files in {base_path}")


def embed_and_upsert(**context):
    conf = context["dag_run"].conf or {}
    vector_db = conf.get("vector_db", "unknown")
    files = context["ti"].xcom_pull(key="files", task_ids="discover_files") or []
    processed = 0
    failed = 0

    for file_path in files:
        try:
            # TODO: real implementation would:
            #   1. Extract text (PyPDF2 / python-docx / pandas / Pillow+OCR)
            #   2. Chunk the text
            #   3. Embed via the configured embedding model
            #   4. Upsert to the vector DB client
            print(f"  [{vector_db}] ingesting {file_path}")
            processed += 1
        except Exception as e:
            print(f"  [{vector_db}] FAILED {file_path}: {e}")
            failed += 1

    context["ti"].xcom_push(key="processed", value=processed)
    context["ti"].xcom_push(key="failed", value=failed)
    print(f"[{vector_db}] processed={processed} failed={failed}")


def callback(**context):
    conf = context["dag_run"].conf or {}
    callback_url = conf.get("callback_url", "")
    if not callback_url:
        print("No callback URL — skipping")
        return

    processed = context["ti"].xcom_pull(key="processed", task_ids="embed_and_upsert") or 0
    failed = context["ti"].xcom_pull(key="failed", task_ids="embed_and_upsert") or 0
    status = "completed" if failed == 0 else "partial"

    payload = {
        "collection_id": conf.get("collection_id"),
        "collection_name": conf.get("collection_name"),
        "vector_db": conf.get("vector_db"),
        "status": status,
        "files_processed": processed,
        "files_failed": failed,
    }

    # Call back to collection_ingest_svc
    base = os.environ.get("INGEST_SVC_URL", "http://host.docker.internal:8007")
    url = f"{base}{callback_url}"
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            print(f"Callback {resp.status}: {resp.read().decode()}")
    except Exception as e:
        print(f"Callback failed: {e}")


with DAG(
    dag_id="collection_ingest_dag",
    default_args=default_args,
    description="Ingest a document collection into a vector DB",
    schedule=None,  # triggered via API only
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["ihcp", "ingest"],
) as dag:
    t1 = PythonOperator(task_id="discover_files", python_callable=discover_files)
    t2 = PythonOperator(task_id="embed_and_upsert", python_callable=embed_and_upsert)
    t3 = PythonOperator(task_id="callback", python_callable=callback)

    t1 >> t2 >> t3
