# slack_svc

The only middleware service that talks to Slack.

## Responsibilities

1. **Outbound notifications** — consumes the `appointment.events` Kafka topic
   produced by `appointment_svc`. On `appointment.booked`, fetches the
   appointment from `appointment_svc` HTTP API and posts a Block Kit message
   with a *Claim* button to `#in-home-help-member-appointment-requests`.
2. **Slack interactivity** — exposes `POST /slack/interactivity` for the
   Slack app to call when a user clicks the *Claim* button. Verifies the
   request signature, calls `POST /appointments/{id}/claim` on
   `appointment_svc` to record the claim in Postgres, then updates the
   original Slack message to show who claimed it.
3. **Slack events** — exposes `POST /slack/events` (Slack Events API). Today
   it handles the URL verification challenge and logs incoming events;
   handlers can be added incrementally.

## Why a separate service

Keeping all Slack I/O in one process means: a Slack outage cannot delay
appointment creation, every Slack call has one consistent retry/backoff
policy, and the Slack app's signing secret + bot token live in exactly one
place. `appointment_svc` stays focused on appointments and never imports the
Slack SDK.

## State

`slack_svc` has no database of its own. All persistent state (claims, slack
message timestamps for dedupe) lives in `appointment_svc` and is reached via
HTTP. That keeps deletes consistent: the consumer re-fetches the appointment
on every Kafka delivery, so anything that changed between produce and
consume is observed before posting.

## Configuration

| Env var | Default | Purpose |
|---|---|---|
| `SLACK_BOT_TOKEN` | — | Slack bot token (`xoxb-...`) used for `chat.postMessage` / `chat.update` |
| `SLACK_SIGNING_SECRET` | — | Validates inbound `/slack/interactivity` and `/slack/events` requests |
| `SLACK_APPOINTMENT_REQUESTS_CHANNEL` | `in-home-help-member-appointment-requests` | Destination channel |
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | Kafka broker |
| `APPOINTMENT_SVC_URL` | `http://127.0.0.1:8004` | Base URL for `appointment_svc` HTTP API |
| `KAFKA_DISABLED` | unset | Set to `1` to skip the Kafka consumer entirely (useful for unit tests) |

## Local development

`slack_svc` is started automatically as part of `npm run local:middleware:start-all`
on port `8009`. To start only this service:

```bash
$HOME/runtime_data/python_venvs/In-Home-Care-Platform/bin/uvicorn slack_svc.main:app \
  --host 127.0.0.1 --port 8009 \
  --app-dir middleware/Microservices/slack_svc/src
```

For Slack to actually reach the interactivity webhook you need a tunnel
(e.g. ngrok) pointing at `http://127.0.0.1:8009`, then configure the
**Request URL** in your Slack app's *Interactivity & Shortcuts* and *Event
Subscriptions* pages to `https://<tunnel>/slack/interactivity` and
`https://<tunnel>/slack/events` respectively.
