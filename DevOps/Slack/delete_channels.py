"""Archive (soft-delete) Slack channels defined in channels.json.

Usage:
    SLACK_BOT_TOKEN=xoxb-... python DevOps/Slack/delete_channels.py
    # or via npm:
    npm run teardown:slack:channels

Slack does not truly delete channels — this archives them. Archived
channels can be unarchived from the Slack UI if needed.

Required bot token scopes:
    channels:manage   — archive public channels
    channels:read     — find channels by name
    groups:write      — archive private channels
    groups:read       — find private channels
"""
from __future__ import annotations

import json
import os
import sys

# Reuse the API helper from create_channels
from create_channels import get_existing_channels, slack_api, CHANNELS_FILE


def main() -> None:
    token = os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        print("ERROR: SLACK_BOT_TOKEN env var not set.")
        sys.exit(1)

    with open(CHANNELS_FILE) as f:
        config = json.load(f)

    channel_names = [ch["name"] for ch in config.get("channels", [])]
    if not channel_names:
        print("No channels defined in channels.json")
        return

    print("Fetching existing channels...")
    existing = get_existing_channels(token)

    print(f"Archiving {len(channel_names)} channel(s):")
    for name in channel_names:
        if name not in existing:
            print(f"  SKIP    #{name} — not found")
            continue
        channel_id = existing[name]
        result = slack_api("conversations.archive", token, {"channel": channel_id})
        if result.get("ok"):
            print(f"  ARCHIVED #{name} ({channel_id})")
        elif result.get("error") == "already_archived":
            print(f"  ALREADY  #{name} ({channel_id})")
        else:
            print(f"  FAILED   #{name}: {result.get('error')}")

    print("\nDone.")


if __name__ == "__main__":
    main()
