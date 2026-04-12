"""Interactive Q&A — answer follow-up questions in Slack threads.

When a field officer replies in a briefing thread (e.g. "What are the
mobility restrictions for this member?"), this module:
  1. Searches the knowledge base with the user's question
  2. Calls the primary LLM with RAG context
  3. Posts the answer as a threaded reply in the same Slack thread
"""
from __future__ import annotations

import logging
import os
from typing import Any

import httpx

from shared.slack import post_message

from .llm_client import chat_completion

log = logging.getLogger(__name__)

API_GATEWAY_URL = os.getenv('API_GATEWAY_URL', 'http://127.0.0.1:8001')

QA_SYSTEM_PROMPT = """You are a care coordinator for an in-home healthcare service.
A field officer is asking a follow-up question about an appointment they just claimed.
Answer concisely based on the knowledge base excerpts below.
If the answer isn't in the excerpts, say so honestly.
Cite sources in brackets like [Source: title]."""


async def handle_qa(
    channel_id: str,
    thread_ts: str,
    user_text: str,
    user_id: str,
) -> None:
    """Search the knowledge base with the user's question and reply in the thread."""

    # 1. RAG search (global — no collection filter since we don't know which appointment)
    rag_chunks: list[dict[str, Any]] = []
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f'{API_GATEWAY_URL}/api/internal/knowledge/search',
                json={'query': user_text, 'top_k': 5},
            )
        if resp.status_code == 200:
            rag_chunks = resp.json().get('results', [])
    except httpx.HTTPError as exc:
        log.warning('qa.rag_failed error=%s', exc)

    # 2. Assemble prompt
    if rag_chunks:
        context_lines = []
        for i, chunk in enumerate(rag_chunks, 1):
            source = chunk.get('item_title') or f'Item #{chunk.get("item_id")}'
            context_lines.append(f'[{i}] Source: "{source}"\n{chunk.get("chunk_text", "")}')
        rag_context = '\n\n'.join(context_lines)
    else:
        rag_context = '(No relevant knowledge base documents found.)'

    user_prompt = f"""Question from field officer: {user_text}

--- Knowledge Base ---
{rag_context}
---

Answer the question concisely."""

    # 3. Call LLM
    try:
        result = chat_completion(QA_SYSTEM_PROMPT, user_prompt)
        answer = result.get('response_text', '')
    except Exception as exc:
        log.error('qa.llm_failed error=%s', exc)
        answer = ''

    if not answer:
        answer = "I couldn't find a relevant answer in the knowledge base for that question."

    # 4. Post as threaded reply
    sources = ', '.join(chunk.get('item_title', '?') for chunk in rag_chunks[:3])
    footer = f'\n_Sources: {sources}_' if sources else ''
    slack_text = answer + footer

    result = post_message(channel_id, text=slack_text, thread_ts=thread_ts)
    if result and result.get('ok'):
        log.info('qa.posted channel=%s thread=%s', channel_id, thread_ts)
    else:
        log.warning('qa.slack_failed error=%s', (result or {}).get('error'))
