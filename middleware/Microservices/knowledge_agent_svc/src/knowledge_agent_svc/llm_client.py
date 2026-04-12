"""LLM client — calls any OpenAI-compatible API (Ollama, OpenAI, Groq, etc).

Uses the standard /v1/chat/completions format which is supported by:
  - Ollama (http://localhost:11434/v1/chat/completions) — free, local
  - OpenAI (https://api.openai.com/v1/chat/completions)
  - Groq (https://api.groq.com/openai/v1/chat/completions)
  - Together (https://api.together.xyz/v1/chat/completions)
  - Any OpenAI-compatible provider

Config via env:
  LLM_API_BASE    default: http://localhost:11434/v1 (Ollama)
  LLM_MODEL       default: llama3
  LLM_API_KEY     default: empty (Ollama doesn't need one)
"""
from __future__ import annotations

import json
import logging
import os
import time
import urllib.error
import urllib.request
from typing import Any

log = logging.getLogger(__name__)

LLM_API_BASE = os.getenv('LLM_API_BASE', 'http://localhost:11434/v1')
LLM_MODEL = os.getenv('LLM_MODEL', 'llama3')
LLM_API_KEY = os.getenv('LLM_API_KEY', '')
LLM_MAX_TOKENS = int(os.getenv('LLM_MAX_TOKENS', '1024'))
LLM_TEMPERATURE = float(os.getenv('LLM_TEMPERATURE', '0.3'))


def chat_completion(
    system_prompt: str,
    user_prompt: str,
    *,
    model: str | None = None,
    api_base: str | None = None,
    api_key: str | None = None,
    max_tokens: int | None = None,
    temperature: float | None = None,
) -> dict[str, Any]:
    """Call an OpenAI-compatible chat completions API.

    Returns {response_text, model, input_tokens, output_tokens,
    total_tokens, latency_ms, finish_reason}.
    """
    base = (api_base or LLM_API_BASE).rstrip('/')
    url = f'{base}/chat/completions'
    mdl = model or LLM_MODEL
    key = api_key or LLM_API_KEY
    max_tok = max_tokens or LLM_MAX_TOKENS
    temp = temperature if temperature is not None else LLM_TEMPERATURE

    headers: dict[str, str] = {'Content-Type': 'application/json'}
    if key:
        headers['Authorization'] = f'Bearer {key}'

    payload = {
        'model': mdl,
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt},
        ],
        'max_tokens': max_tok,
        'temperature': temp,
    }

    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=headers, method='POST')

    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode('utf-8', 'ignore')
        log.error('llm.http_error url=%s status=%d body=%s', url, exc.code, error_body[:500])
        raise
    except (urllib.error.URLError, TimeoutError) as exc:
        log.error('llm.network_error url=%s error=%s', url, exc)
        raise

    latency_ms = int((time.time() - t0) * 1000)

    choices = body.get('choices', [])
    response_text = choices[0]['message']['content'] if choices else ''
    finish_reason = choices[0].get('finish_reason', '') if choices else ''

    usage = body.get('usage', {})
    input_tokens = usage.get('prompt_tokens', 0)
    output_tokens = usage.get('completion_tokens', 0)
    total_tokens = usage.get('total_tokens', input_tokens + output_tokens)

    log.info(
        'llm.response model=%s input_tokens=%d output_tokens=%d latency_ms=%d',
        mdl, input_tokens, output_tokens, latency_ms,
    )

    return {
        'response_text': response_text,
        'model': mdl,
        'provider': _detect_provider(base),
        'input_tokens': input_tokens,
        'output_tokens': output_tokens,
        'total_tokens': total_tokens,
        'latency_ms': latency_ms,
        'finish_reason': finish_reason,
    }


def _detect_provider(api_base: str) -> str:
    if 'openai.com' in api_base:
        return 'openai'
    if 'anthropic.com' in api_base:
        return 'anthropic'
    if 'groq.com' in api_base:
        return 'groq'
    if 'together' in api_base:
        return 'together'
    if 'localhost' in api_base or '127.0.0.1' in api_base:
        return 'ollama'
    return 'unknown'
