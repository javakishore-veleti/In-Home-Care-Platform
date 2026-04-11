# Slack channel automation

Scripts to create, check, and archive the four In-Home-Care-Platform
Slack channels. All channels are defined in `channels.json` — add or
remove entries there and re-run.

## Channels

| Channel | Persona | Purpose |
|---|---|---|
| `#in-home-help-field-officers` | Field staff | Visit questions, care plans, scheduling |
| `#in-home-help-customer-support` | Support agents | Disputes, member lookup, policy |
| `#in-home-help-product-owners` | Product owners | Metrics, feature requests, ops |
| `#in-home-help-customers` | Members/patients | Appointment status, visit history, care plans |

## Prerequisites

1. Create a Slack app at https://api.slack.com/apps
2. Add these bot token scopes:
   - `channels:manage` — create/archive public channels
   - `channels:read` — list channels
   - `groups:write` — create/archive private channels
   - `groups:read` — list private channels
   - `chat:write` — (for the LangGraph bot to reply later)
3. Install the app to your workspace
4. Copy the Bot User OAuth Token (`xoxb-...`)
5. Export it:

```bash
export SLACK_BOT_TOKEN=xoxb-your-token-here
```

## Commands (via npm)

```bash
# Create all 4 channels (idempotent — safe to re-run)
npm run setup:slack:channels

# Check status of all 4 channels
npm run status:slack:channels

# Archive all 4 channels (soft-delete)
npm run teardown:slack:channels
```

## How it works

- `create_channels.py` reads `channels.json`, calls `conversations.create`
  for each channel (skips if it already exists), then sets the purpose
  and topic. Fully idempotent.
- `status_channels.py` lists each channel with its status (ACTIVE /
  ARCHIVED / NOT FOUND) and member count.
- `delete_channels.py` archives each channel. Slack doesn't truly
  delete channels — archived channels can be unarchived from the UI.

No external Python packages required — uses only `urllib` from the
standard library so it works without activating the conda venv.
