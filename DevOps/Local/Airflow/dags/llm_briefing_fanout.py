"""Airflow DAG: LLM briefing fan-out for appointment claims.

Production version of the inline parallel fan-out in
knowledge_agent_svc/briefing.py. Each enabled model gets its own
Airflow task, all run in parallel via the task group. Per-task retries,
monitoring via the Airflow UI, and DAG-level timeouts.

Triggered externally (via Airflow REST API or a Kafka sensor) with
conf: {"appointment_id": 42, "slack_channel_id": "C...", "slack_message_ts": "..."}

For local dev, the inline fan-out in knowledge_agent_svc is simpler
and adequate. This DAG is for production deployments where you need
Airflow's retry/monitoring/parallelism infrastructure.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator

REGISTRY_PATH = os.getenv(
    'LLM_MODELS_REGISTRY',
    str(Path(__file__).resolve().parent.parent / 'Seeds' / 'llm-models-registry.json'),
)

default_args = {
    'owner': 'knowledge_agent',
    'retries': 2,
    'retry_delay': timedelta(seconds=30),
    'execution_timeout': timedelta(minutes=5),
}


def _load_models():
    try:
        with open(REGISTRY_PATH) as f:
            data = json.load(f)
        return [m for m in data.get('models', []) if m.get('enabled')]
    except Exception:
        return []


def _rag_search(**ctx):
    """Shared RAG search — results passed to all model tasks via XCom."""
    import urllib.request
    conf = ctx['dag_run'].conf or {}
    appointment_id = conf.get('appointment_id')
    api_gw = os.getenv('API_GATEWAY_URL', 'http://127.0.0.1:8001')

    # Fetch appointment
    req = urllib.request.Request(f'{api_gw}/api/internal/knowledge/search', method='POST',
                                headers={'Content-Type': 'application/json'},
                                data=json.dumps({'query': 'care briefing', 'top_k': 5}).encode())
    with urllib.request.urlopen(req, timeout=30) as resp:
        results = json.loads(resp.read())
    ctx['ti'].xcom_push(key='rag_results', value=results.get('results', []))
    ctx['ti'].xcom_push(key='appointment_id', value=appointment_id)


def _call_model(model_config: dict, **ctx):
    """Call one LLM model with the shared RAG context."""
    import urllib.request
    rag_results = ctx['ti'].xcom_pull(key='rag_results', task_ids='rag_search')
    appointment_id = ctx['ti'].xcom_pull(key='appointment_id', task_ids='rag_search')

    api_base = model_config.get('api_base', '')
    model_id = model_config.get('model_id', '')
    api_key = os.getenv(model_config.get('env_key', ''), '') if model_config.get('env_key') else ''

    context = '\n'.join(r.get('chunk_text', '') for r in (rag_results or []))
    payload = {
        'model': model_id,
        'messages': [
            {'role': 'system', 'content': 'You are a care coordinator. Write a concise briefing.'},
            {'role': 'user', 'content': f'Context:\n{context}\n\nWrite a briefing.'},
        ],
        'max_tokens': 1024,
        'temperature': 0.3,
    }

    headers = {'Content-Type': 'application/json'}
    if api_key:
        headers['Authorization'] = f'Bearer {api_key}'

    req = urllib.request.Request(f'{api_base}/chat/completions', method='POST',
                                headers=headers, data=json.dumps(payload).encode())
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read())

    response_text = result.get('choices', [{}])[0].get('message', {}).get('content', '')
    ctx['ti'].xcom_push(key=f'response_{model_config["id"]}', value=response_text)


def _post_primary(**ctx):
    """Post the primary model's response to Slack."""
    conf = ctx['dag_run'].conf or {}
    channel = conf.get('slack_channel_id')
    thread_ts = conf.get('slack_message_ts')
    if not channel or not thread_ts:
        return

    models = _load_models()
    primary = next((m for m in models if m.get('is_primary')), models[0] if models else None)
    if not primary:
        return

    response_text = ctx['ti'].xcom_pull(key=f'response_{primary["id"]}', task_ids=f'call_{primary["id"]}')
    if not response_text:
        return

    import urllib.request
    token = os.getenv('SLACK_BOT_TOKEN', '')
    payload = {'channel': channel, 'text': response_text, 'thread_ts': thread_ts}
    req = urllib.request.Request('https://slack.com/api/chat.postMessage', method='POST',
                                headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
                                data=json.dumps(payload).encode())
    urllib.request.urlopen(req, timeout=10)


with DAG(
    'llm_briefing_fanout',
    default_args=default_args,
    description='Fan out RAG-augmented prompts to all enabled LLMs on appointment claim',
    schedule_interval=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['llm', 'knowledge', 'briefing'],
) as dag:

    rag_task = PythonOperator(task_id='rag_search', python_callable=_rag_search)

    models = _load_models()
    model_tasks = []
    for model in models:
        task = PythonOperator(
            task_id=f'call_{model["id"]}',
            python_callable=_call_model,
            op_kwargs={'model_config': model},
        )
        rag_task >> task
        model_tasks.append(task)

    post_task = PythonOperator(task_id='post_primary_to_slack', python_callable=_post_primary)
    for mt in model_tasks:
        mt >> post_task
