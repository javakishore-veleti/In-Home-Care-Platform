"""Knowledge briefing flow — triggered on appointment.claimed.

Pipeline:
  1. Fetch the appointment from appointment_svc (get service_type)
  2. RAG search the matching collection for relevant chunks
  3. Assemble a prompt with RAG context
  4. Call the LLM
  5. Post the briefing as a Slack threaded reply
  6. Store the response in the DB (Phase 3c — for now just log)
"""
from __future__ import annotations

import logging
import os
from typing import Any

import httpx

from shared.slack import post_message

from .llm_client import chat_completion

log = logging.getLogger(__name__)

APPOINTMENT_SVC_URL = os.getenv('APPOINTMENT_SVC_URL', 'http://127.0.0.1:8004')
API_GATEWAY_URL = os.getenv('API_GATEWAY_URL', 'http://127.0.0.1:8001')
HTTP_TIMEOUT = 10

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


async def run_briefing(event: dict[str, Any]) -> bool:
    """Execute the full briefing pipeline for one claimed appointment.

    Returns True on success (commit Kafka offset), False on transient
    failure (retry on next poll).
    """
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
        log.warning('briefing.fetch_appointment_failed id=%d error=%s', appointment_id, exc)
        return False

    service_type = appointment.get('service_type', '')
    member_id = appointment.get('member_id')
    requested_date = appointment.get('requested_date', '')
    time_slot = appointment.get('requested_time_slot', '')

    # 2. RAG search
    collection_slug = _slugify(service_type)
    rag_chunks: list[dict[str, Any]] = []
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f'{API_GATEWAY_URL}/api/internal/knowledge/search',
                json={
                    'query': f'What should a field officer know before a {service_type} visit?',
                    'collection_slug': collection_slug,
                    'top_k': 5,
                },
            )
        if resp.status_code == 200:
            rag_chunks = resp.json().get('results', [])
    except httpx.HTTPError as exc:
        log.warning('briefing.rag_search_failed slug=%s error=%s', collection_slug, exc)

    # 3. Assemble prompt
    if rag_chunks:
        context_lines = []
        for i, chunk in enumerate(rag_chunks, 1):
            source = chunk.get('item_title') or f'Item #{chunk.get("item_id")}'
            text = chunk.get('chunk_text', '')
            context_lines.append(f'[{i}] Source: "{source}"\n{text}')
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

    # 4. Call LLM
    try:
        llm_result = chat_completion(SYSTEM_PROMPT, user_prompt)
        briefing_text = llm_result.get('response_text', '')
    except Exception as exc:
        log.error('briefing.llm_failed id=%d error=%s', appointment_id, exc)
        briefing_text = None

    if not briefing_text:
        log.warning('briefing.no_response id=%d', appointment_id)
        return True

    # 5. Post to Slack as threaded reply
    if slack_channel_id and slack_message_ts:
        header = f'*Care briefing — {service_type}*\n\n'
        sources = '\n'.join(
            f'_{chunk.get("item_title", "?")}_' for chunk in rag_chunks[:5]
        )
        footer = f'\n\n_Sources: {sources}_' if sources else ''
        slack_text = header + briefing_text + footer

        result = post_message(
            slack_channel_id,
            text=slack_text,
            thread_ts=slack_message_ts,
        )
        if result and result.get('ok'):
            log.info(
                'briefing.posted appointment_id=%d channel=%s model=%s tokens=%d latency=%dms',
                appointment_id, slack_channel_id,
                llm_result.get('model'), llm_result.get('total_tokens', 0),
                llm_result.get('latency_ms', 0),
            )
        else:
            log.warning('briefing.slack_post_failed id=%d error=%s', appointment_id, (result or {}).get('error'))
    else:
        log.info('briefing.no_slack_thread id=%d (no channel/ts in event)', appointment_id)

    # 6. Log the response (Phase 3c stores in llm_responses table)
    log.info(
        'briefing.done appointment_id=%d service_type=%s model=%s input_tokens=%d output_tokens=%d',
        appointment_id, service_type,
        llm_result.get('model'), llm_result.get('input_tokens', 0),
        llm_result.get('output_tokens', 0),
    )
    return True


def _slugify(name: str) -> str:
    import re
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-') or 'unknown'
