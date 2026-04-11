"""Lightweight Slack Web API + interactivity helpers used by slack_svc.

Stdlib only — no slack_sdk dependency. Reads SLACK_BOT_TOKEN and
SLACK_SIGNING_SECRET from the environment. All functions are best-effort:
network or config failures log and return None so the caller can decide
whether to retry.

Domain-specific Block Kit rendering (e.g. appointment cards) lives in the
service that owns the domain — this module stays generic.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import time
import urllib.error
import urllib.request
from typing import Any

log = logging.getLogger(__name__)

SLACK_API_BASE = 'https://slack.com/api'


def get_bot_token() -> str | None:
    return os.getenv('SLACK_BOT_TOKEN') or None


def get_signing_secret() -> str | None:
    return os.getenv('SLACK_SIGNING_SECRET') or None


def _call(method: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    token = get_bot_token()
    if not token:
        log.info('slack.skip', extra={'reason': 'SLACK_BOT_TOKEN not set', 'method': method})
        return None
    url = f'{SLACK_API_BASE}/{method}'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json; charset=utf-8',
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = json.loads(resp.read().decode('utf-8'))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        log.warning('slack.call_failed', extra={'method': method, 'error': str(exc)})
        return None
    if not body.get('ok'):
        log.warning('slack.api_error', extra={'method': method, 'error': body.get('error')})
    return body


def post_message(channel: str, text: str, blocks: list[dict[str, Any]] | None = None) -> dict[str, Any] | None:
    payload: dict[str, Any] = {'channel': channel, 'text': text}
    if blocks is not None:
        payload['blocks'] = blocks
    return _call('chat.postMessage', payload)


def update_message(
    channel: str,
    ts: str,
    text: str,
    blocks: list[dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    payload: dict[str, Any] = {'channel': channel, 'ts': ts, 'text': text}
    if blocks is not None:
        payload['blocks'] = blocks
    return _call('chat.update', payload)


def verify_signature(headers: dict[str, str], raw_body: bytes) -> bool:
    """Validate Slack request signature per https://api.slack.com/authentication/verifying-requests-from-slack."""
    secret = get_signing_secret()
    if not secret:
        log.warning('slack.verify_skip', extra={'reason': 'SLACK_SIGNING_SECRET not set'})
        return False
    timestamp = headers.get('x-slack-request-timestamp') or headers.get('X-Slack-Request-Timestamp')
    signature = headers.get('x-slack-signature') or headers.get('X-Slack-Signature')
    if not timestamp or not signature:
        return False
    try:
        ts_int = int(timestamp)
    except ValueError:
        return False
    if abs(time.time() - ts_int) > 60 * 5:
        return False
    basestring = f'v0:{timestamp}:{raw_body.decode("utf-8")}'.encode('utf-8')
    digest = hmac.new(secret.encode('utf-8'), basestring, hashlib.sha256).hexdigest()
    expected = f'v0={digest}'
    return hmac.compare_digest(expected, signature)
