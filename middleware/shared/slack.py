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
        # Inline the values in the message text so they survive default
        # Python logging (which silently drops the `extra` dict).
        log.warning('slack.call_failed method=%s error=%s', method, str(exc))
        return None
    if not body.get('ok'):
        err = body.get('error')
        # Hint at the most common fixes inline so the log line is
        # actionable without having to dig into Slack's API docs.
        hint = ''
        if err == 'not_in_channel':
            hint = ' (invite the bot to the channel: /invite @your_bot)'
        elif err == 'channel_not_found':
            hint = ' (channel id/name does not exist or bot lacks visibility)'
        elif err == 'invalid_auth' or err == 'token_revoked':
            hint = ' (SLACK_BOT_TOKEN is invalid or revoked)'
        elif err == 'missing_scope':
            hint = f' (bot token is missing required scope: needed={body.get("needed")}, provided={body.get("provided")})'
        log.warning('slack.api_error method=%s error=%s%s', method, err, hint)
    return body


def post_message(channel: str, text: str, blocks: list[dict[str, Any]] | None = None) -> dict[str, Any] | None:
    payload: dict[str, Any] = {'channel': channel, 'text': text}
    if blocks is not None:
        payload['blocks'] = blocks
    return _call('chat.postMessage', payload)


def list_channels(types: str = 'public_channel,private_channel', limit: int = 200) -> list[dict[str, Any]]:
    """Return every Slack channel the bot can see, with is_member flags.

    Auto-paginates so callers don't have to chase cursors. Returns an
    empty list on any failure (logged) so callers can render an empty
    state instead of bubbling errors to the user.
    """
    channels: list[dict[str, Any]] = []
    cursor: str | None = None
    while True:
        payload: dict[str, Any] = {'types': types, 'limit': limit, 'exclude_archived': True}
        if cursor:
            payload['cursor'] = cursor
        result = _call('conversations.list', payload)
        if not result or not result.get('ok'):
            break
        channels.extend(result.get('channels') or [])
        cursor = (result.get('response_metadata') or {}).get('next_cursor') or None
        if not cursor:
            break
    return channels


def invite_user_to_channel(channel_id: str, user_id: str) -> dict[str, Any] | None:
    """Invite ``user_id`` (typically the bot's own user id) into a channel."""
    return _call('conversations.invite', {'channel': channel_id, 'users': user_id})


def auth_test() -> dict[str, Any] | None:
    """Return the bot's identity (user_id, team, etc.) — used to discover
    the bot user id so the admin portal can self-invite the bot to a
    channel without the user having to look it up."""
    return _call('auth.test', {})


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
