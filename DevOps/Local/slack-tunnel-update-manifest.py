#!/usr/bin/env python3
"""Push the local tunnel's public URL into a Slack app manifest.

Called by `DevOps/Local/slack-tunnel.sh up` when SLACK_APP_ID and
SLACK_APP_CONFIG_TOKEN are set in .env.local. Without those, the
tunnel script just prints the URL and the user pastes it into the
Slack admin pages by hand.

Flow:
  1. apps.manifest.export             — fetch the current manifest
  2. patch interactivity.request_url
     and event_subscriptions.request_url with the new tunnel URL
  3. apps.manifest.update             — write it back

Requires `app_configurations:write` on the configuration token, which
is what Slack returns by default for tokens generated at
https://api.slack.com/apps -> Manage Distribution -> App Configuration
Tokens.

Stdlib only — no slack_sdk dependency, matches the rest of the local
shared/slack.py module.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from typing import Any

SLACK_API_BASE = 'https://slack.com/api'


def slack_call(method: str, token: str, payload: dict[str, Any]) -> dict[str, Any]:
    url = f'{SLACK_API_BASE}/{method}'
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json; charset=utf-8',
        },
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as exc:
        return {'ok': False, 'error': f'http {exc.code}', 'detail': exc.read().decode('utf-8', 'ignore')}
    except urllib.error.URLError as exc:
        return {'ok': False, 'error': f'urlopen failed: {exc.reason}'}
    return body


def patch_manifest(manifest: dict[str, Any], interactivity_url: str, events_url: str) -> dict[str, Any]:
    """Set both request URLs on the manifest, creating the keys if they don't exist."""
    settings = manifest.setdefault('settings', {})
    interactivity = settings.setdefault('interactivity', {})
    interactivity['is_enabled'] = True
    interactivity['request_url'] = interactivity_url

    events = settings.setdefault('event_subscriptions', {})
    events['request_url'] = events_url
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--app-id', required=True)
    parser.add_argument('--token', required=True, help='SLACK_APP_CONFIG_TOKEN')
    parser.add_argument('--interactivity-url', required=True)
    parser.add_argument('--events-url', required=True)
    args = parser.parse_args()

    print(f'  fetching current manifest for app {args.app_id}...')
    export = slack_call('apps.manifest.export', args.token, {'app_id': args.app_id})
    if not export.get('ok'):
        print(f'  apps.manifest.export failed: {export.get("error")}')
        if export.get('detail'):
            print(f'  detail: {export["detail"]}')
        return 1

    manifest = export.get('manifest')
    if not isinstance(manifest, dict):
        print(f'  apps.manifest.export returned no manifest: {export}')
        return 1

    patched = patch_manifest(manifest, args.interactivity_url, args.events_url)

    print('  pushing updated manifest...')
    update = slack_call(
        'apps.manifest.update',
        args.token,
        {'app_id': args.app_id, 'manifest': patched},
    )
    if not update.get('ok'):
        print(f'  apps.manifest.update failed: {update.get("error")}')
        if update.get('detail'):
            print(f'  detail: {update["detail"]}')
        return 1

    print(f'  interactivity.request_url     = {args.interactivity_url}')
    print(f'  event_subscriptions.request_url = {args.events_url}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
