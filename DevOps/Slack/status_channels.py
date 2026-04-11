"""Check status of Slack channels defined in channels.json.

Usage:
    SLACK_BOT_TOKEN=xoxb-... python DevOps/Slack/status_channels.py
    # or via npm:
    npm run status:slack:channels
"""
from __future__ import annotations

import json
import os
import sys

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

    print(f"\nChannel status ({len(channel_names)} configured):\n")
    print(f"  {'Channel':<40} {'Status':<12} {'ID'}")
    print(f"  {'─'*40} {'─'*12} {'─'*15}")
    for name in channel_names:
        if name in existing:
            channel_id = existing[name]
            # Check if archived
            info = slack_api("conversations.info", token, {"channel": channel_id})
            if info.get("ok"):
                archived = info["channel"].get("is_archived", False)
                members = info["channel"].get("num_members", 0)
                status = "ARCHIVED" if archived else f"ACTIVE ({members} members)"
            else:
                status = "EXISTS"
            print(f"  #{name:<39} {status:<12} {channel_id}")
        else:
            print(f"  #{name:<39} {'NOT FOUND':<12} —")

    print()


if __name__ == "__main__":
    main()
