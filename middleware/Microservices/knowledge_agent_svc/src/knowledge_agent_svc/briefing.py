"""Knowledge briefing flow — multi-model parallel fan-out.

On appointment.claimed:
  1. Fetch appointment → service_type
  2. RAG search → top chunks
  3. Assemble prompt
  4. Fan out to ALL enabled models in parallel (asyncio.gather)
  5. Store each response in llm_responses table
  6. Post the PRIMARY model's response as a Slack threaded reply
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import httpx

from shared.slack import post_message
from shared.storage import get_database_url, now_utc

from .llm_client import chat_completion

log = logging.getLogger(__name__)

APPOINTMENT_SVC_URL = os.getenv('APPOINTMENT_SVC_URL', 'http://127.0.0.1:8004')
API_GATEWAY_URL = os.getenv('API_GATEWAY_URL', 'http://127.0.0.1:8001')
HTTP_TIMEOUT = 10

REGISTRY_PATH = os.getenv(
    'LLM_MODELS_REGISTRY',
    str(Path(__file__).resolve().parent.parent.parent.parent.parent / 'DevOps' / 'Seeds' / 'llm-models-registry.json'),
)

_executor = ThreadPoolExecutor(max_workers=5)

SYSTEM_PROMPT = """You are a care coordinator for an in-home healthcare service.
A field officer just claimed an appointment. Based on the knowledge base
excerpts below and the appointment details, write a concise briefing
(3 short paragraphs) that the field officer should read before the visit.

Prioritize:
1. Safety protocols and compliance requirements
2. Key clinical procedures for this service type
3. Any recent announcements or policy changes

Be concise — the field officer reads this on their phone in Slack.
Cite the source document title for each key fact in brackets like [Source: title]."""


def _load_enabled_models() -> list[dict[str, Any]]:
    try:
        with open(REGISTRY_PATH) as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        log.warning('briefing.registry_load_failed path=%s error=%s', REGISTRY_PATH, exc)
        return []
    models = []
    for m in data.get('models', []):
        if not m.get('enabled'):
            continue
        env_key = m.get('env_key')
        if env_key and not os.getenv(env_key):
            continue
        models.append(m)
    return models


def _store_response(
    appointment_id: int,
    model: dict[str, Any],
    system_prompt: str,
    user_prompt: str,
    rag_chunks_used: int,
    llm_result: dict[str, Any],
    is_primary: bool,
    service_type: str,
    collection_slug: str,
) -> None:
    try:
        import psycopg
        from psycopg.rows import dict_row
        db_url = get_database_url()
        input_cost = (llm_result.get('input_tokens', 0) / 1000) * model.get('input_cost_per_1k', 0)
        output_cost = (llm_result.get('output_tokens', 0) / 1000) * model.get('output_cost_per_1k', 0)
        with psycopg.connect(db_url, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    '''INSERT INTO knowledge_schema.llm_responses
                        (appointment_id, model_id, provider, display_name,
                         system_prompt, user_prompt, rag_chunks_used,
                         response_text, finish_reason,
                         input_tokens, output_tokens, total_tokens,
                         input_cost_usd, output_cost_usd, total_cost_usd,
                         latency_ms, is_primary, service_type, collection_slug)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
                    (
                        appointment_id,
                        model.get('id'),
                        model.get('provider'),
                        model.get('display_name'),
                        system_prompt,
                        user_prompt,
                        rag_chunks_used,
                        llm_result.get('response_text', ''),
                        llm_result.get('finish_reason', ''),
                        llm_result.get('input_tokens', 0),
                        llm_result.get('output_tokens', 0),
                        llm_result.get('total_tokens', 0),
                        round(input_cost, 6),
                        round(output_cost, 6),
                        round(input_cost + output_cost, 6),
                        llm_result.get('latency_ms', 0),
                        is_primary,
                        service_type,
                        collection_slug,
                    ),
                )
    except Exception as exc:
        log.warning('briefing.store_failed model=%s error=%s', model.get('id'), exc)


def _call_model_sync(model: dict[str, Any], system_prompt: str, user_prompt: str) -> dict[str, Any]:
    """Synchronous LLM call — runs in thread pool for parallelism."""
    from .metrics import LLM_REQUESTS, LLM_TOKENS_INPUT, LLM_TOKENS_OUTPUT, LLM_COST_USD, LLM_LATENCY

    model_id = model.get('id', 'unknown')
    provider = model.get('provider', 'unknown')

    try:
        result = chat_completion(
            system_prompt,
            user_prompt,
            model=model.get('model_id'),
            api_base=model.get('api_base'),
            api_key=os.getenv(model.get('env_key', ''), '') if model.get('env_key') else '',
            max_tokens=1024,
            temperature=0.3,
        )
        result['model_config'] = model
        # Emit Prometheus metrics
        LLM_REQUESTS.labels(model_id=model_id, provider=provider, status='success').inc()
        LLM_TOKENS_INPUT.labels(model_id=model_id, provider=provider).inc(result.get('input_tokens', 0))
        LLM_TOKENS_OUTPUT.labels(model_id=model_id, provider=provider).inc(result.get('output_tokens', 0))
        input_cost = (result.get('input_tokens', 0) / 1000) * model.get('input_cost_per_1k', 0)
        output_cost = (result.get('output_tokens', 0) / 1000) * model.get('output_cost_per_1k', 0)
        LLM_COST_USD.labels(model_id=model_id, provider=provider).inc(input_cost + output_cost)
        LLM_LATENCY.labels(model_id=model_id, provider=provider).observe(result.get('latency_ms', 0) / 1000)
        return result
    except Exception as exc:
        LLM_REQUESTS.labels(model_id=model_id, provider=provider, status='error').inc()
        log.warning('briefing.model_failed model=%s error=%s', model.get('id'), exc)
        return {
            'model_config': model,
            'response_text': '',
            'error': str(exc),
            'input_tokens': 0,
            'output_tokens': 0,
            'total_tokens': 0,
            'latency_ms': 0,
            'finish_reason': 'error',
        }


async def run_briefing(event: dict[str, Any]) -> bool:
    """Multi-model parallel briefing for one claimed appointment."""
    appointment_id = event.get('appointment_id')
    slack_channel_id = event.get('slack_channel_id')
    slack_message_ts = event.get('slack_message_ts')

    if not appointment_id:
        log.warning('briefing.missing_appointment_id')
        return True

    # 1. Fetch appointment
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            resp = await client.get(f'{APPOINTMENT_SVC_URL}/appointments/{appointment_id}')
        if resp.status_code == 404:
            log.info('briefing.appointment_gone id=%d', appointment_id)
            return True
        resp.raise_for_status()
        appointment = resp.json()
    except httpx.HTTPError as exc:
        log.warning('briefing.fetch_failed id=%d error=%s', appointment_id, exc)
        return False

    service_type = appointment.get('service_type', '')
    member_id = appointment.get('member_id')
    requested_date = appointment.get('requested_date', '')
    time_slot = appointment.get('requested_time_slot', '')
    collection_slug = _slugify(service_type)

    # 2. RAG search
    rag_chunks: list[dict[str, Any]] = []
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f'{API_GATEWAY_URL}/api/internal/knowledge/search',
                json={'query': f'What should a field officer know before a {service_type} visit?',
                      'collection_slug': collection_slug, 'top_k': 5},
            )
        if resp.status_code == 200:
            rag_chunks = resp.json().get('results', [])
    except httpx.HTTPError as exc:
        log.warning('briefing.rag_failed slug=%s error=%s', collection_slug, exc)

    # 3. Assemble prompt
    if rag_chunks:
        context_lines = []
        for i, chunk in enumerate(rag_chunks, 1):
            source = chunk.get('item_title') or f'Item #{chunk.get("item_id")}'
            context_lines.append(f'[{i}] Source: "{source}"\n{chunk.get("chunk_text", "")}')
        rag_context = '\n\n'.join(context_lines)
    else:
        rag_context = '(No knowledge base documents found for this service type.)'

    user_prompt = f"""Service type: {service_type}
Appointment date: {requested_date} ({time_slot})
Member ID: M-{member_id}

--- Knowledge Base ({service_type}) ---
{rag_context}
---

Write the briefing for the field officer."""

    # 4. Load enabled models + fan out in parallel
    models = _load_enabled_models()
    if not models:
        log.warning('briefing.no_models_enabled')
        return True

    log.info('briefing.fanout appointment_id=%d models=%d names=%s',
             appointment_id, len(models), [m['id'] for m in models])

    loop = asyncio.get_event_loop()
    tasks = [
        loop.run_in_executor(_executor, _call_model_sync, model, SYSTEM_PROMPT, user_prompt)
        for model in models
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 5. Store each response + find primary
    primary_response = None
    for res in results:
        if isinstance(res, Exception):
            log.warning('briefing.gather_exception error=%s', res)
            continue
        model_cfg = res.get('model_config', {})
        is_primary = model_cfg.get('is_primary', False)
        if res.get('response_text'):
            _store_response(
                appointment_id, model_cfg, SYSTEM_PROMPT, user_prompt,
                len(rag_chunks), res, is_primary, service_type, collection_slug,
            )
            if is_primary and res.get('response_text'):
                primary_response = res
            elif primary_response is None and res.get('response_text'):
                primary_response = res

    # 6. Post PRIMARY response as Slack threaded reply
    if primary_response and slack_channel_id and slack_message_ts:
        model_name = primary_response.get('model_config', {}).get('display_name', 'AI')
        header = f'*Care briefing — {service_type}*\n_via {model_name}_\n\n'
        sources = ', '.join(chunk.get('item_title', '?') for chunk in rag_chunks[:5])
        footer = f'\n\n_Sources: {sources}_' if sources else ''
        slack_text = header + primary_response.get('response_text', '') + footer

        result = post_message(slack_channel_id, text=slack_text, thread_ts=slack_message_ts)
        if result and result.get('ok'):
            log.info('briefing.posted appointment_id=%d model=%s', appointment_id,
                     primary_response.get('model_config', {}).get('id'))
        else:
            log.warning('briefing.slack_failed id=%d error=%s', appointment_id, (result or {}).get('error'))

    successful = sum(1 for r in results if not isinstance(r, Exception) and r.get('response_text'))
    log.info('briefing.done appointment_id=%d models_called=%d successful=%d',
             appointment_id, len(models), successful)
    return True


def _slugify(name: str) -> str:
    import re
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-') or 'unknown'
