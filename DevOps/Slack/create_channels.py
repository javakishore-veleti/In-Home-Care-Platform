"""Create (or verify) Slack channels defined in channels.json.

Usage:
    SLACK_BOT_TOKEN=xoxb-... python DevOps/Slack/create_channels.py
    # or via npm:
    npm run setup:slack:channels

Required bot token scopes:
    channels:manage   — create public channels
    channels:read     — check if a channel already exists
    groups:write      — create private channels (if needed)
    groups:read       — check private channel existence

The script is idempotent: if a channel already exists it sets the
purpose and topic without failing.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
import urllib.error

CHANNELS_FILE = os.path.join(os.path.dirname(__file__), "channels.json")
BASE_URL = "https://slack.com/api"


def slack_api(method: str, token: str, payload: dict | None = None) -> dict:
    """Call one Slack Web API method. Returns the parsed JSON response."""
    url = f"{BASE_URL}/{method}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8",
    }
    data = json.dumps(payload or {}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_existing_channels(token: str) -> dict[str, str]:
    """Return {channel_name: channel_id} for all channels the bot can see."""
    channels: dict[str, str] = {}
    cursor = None
    while True:
        payload: dict = {"limit": 200, "types": "public_channel,private_channel"}
        if cursor:
            payload["cursor"] = cursor
        result = slack_api("conversations.list", token, payload)
        if not result.get("ok"):
            print(f"  WARNING: conversations.list failed: {result.get('error')}")
            break
        for ch in result.get("channels", []):
            channels[ch["name"]] = ch["id"]
        cursor = result.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            break
    return channels


def create_or_update_channel(
    token: str,
    name: str,
    purpose: str,
    topic: str,
    existing: dict[str, str],
) -> str:
    """Create the channel if it doesn't exist, then set purpose + topic.
    Returns the channel ID.
    """
    if name in existing:
        channel_id = existing[name]
        print(f"  EXISTS  #{name} ({channel_id})")
    else:
        result = slack_api("conversations.create", token, {"name": name})
        if result.get("ok"):
            channel_id = result["channel"]["id"]
            print(f"  CREATED #{name} ({channel_id})")
        elif result.get("error") == "name_taken":
            # Race condition or visibility issue — fetch ID
            channel_id = existing.get(name, "unknown")
            print(f"  EXISTS  #{name} (name_taken, id={channel_id})")
        else:
            print(f"  FAILED  #{name}: {result.get('error')}")
            return ""

    # Set purpose
    slack_api("conversations.setPurpose", token, {
        "channel": channel_id, "purpose": purpose,
    })
    # Set topic
    slack_api("conversations.setTopic", token, {
        "channel": channel_id, "topic": topic,
    })
    return channel_id


def main() -> None:
    token = os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        print("ERROR: SLACK_BOT_TOKEN env var not set.")
        print("  export SLACK_BOT_TOKEN=xoxb-your-bot-token")
        print("  npm run setup:slack:channels")
        sys.exit(1)

    with open(CHANNELS_FILE) as f:
        config = json.load(f)

    channels = config.get("channels", [])
    if not channels:
        print("No channels defined in channels.json")
        return

    print(f"Fetching existing channels...")
    existing = get_existing_channels(token)
    print(f"  Found {len(existing)} existing channels")
    print()

    print(f"Processing {len(channels)} channel(s):")
    created = 0
    for ch in channels:
        result = create_or_update_channel(
            token,
            ch["name"],
            ch.get("purpose", ""),
            ch.get("topic", ""),
            existing,
        )
        if result:
            created += 1

    print()
    print(f"Done. {created}/{len(channels)} channels ready.")


if __name__ == "__main__":
    main()
