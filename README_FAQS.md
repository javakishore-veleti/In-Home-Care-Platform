# In-Home-Care-Platform — Setup FAQs

Every issue that came up while getting the stack running end-to-end on a
fresh laptop — Docker, Kafka, ngrok, Slack app config, the admin portal,
service restarts. Each FAQ is phrased the way it actually showed up
(error message, symptom, or question), followed by the root cause and
the fix.

If you hit something that isn't here yet, add it as a new entry in the
same format and keep the Table of Contents in sync.

## Table of Contents

- [1. First-run setup](#1-first-run-setup)
  - [1.1 How do I bring the whole stack up for the first time?](#11-how-do-i-bring-the-whole-stack-up-for-the-first-time)
  - [1.2 What goes in `.env.local`?](#12-what-goes-in-envlocal)
  - [1.3 How do I tear everything down cleanly (including DB state)?](#13-how-do-i-tear-everything-down-cleanly-including-db-state)
  - [1.4 `stop-all` vs `shutdown-all` — which do I use?](#14-stop-all-vs-shutdown-all--which-do-i-use)
- [2. Docker / Postgres / Kafka](#2-docker--postgres--kafka)
  - [2.1 `psycopg2.OperationalError: server closed the connection unexpectedly`](#21-psycopg2operationalerror-server-closed-the-connection-unexpectedly)
  - [2.2 `docker compose down` keeps Postgres / Kafka data around](#22-docker-compose-down-keeps-postgres--kafka-data-around)
  - [2.3 Kafka container in a restart loop: `advertised.listeners cannot use the nonroutable meta-address 0.0.0.0`](#23-kafka-container-in-a-restart-loop-advertisedlisteners-cannot-use-the-nonroutable-meta-address-00000)
  - [2.4 `kafka-ui` shows `status: initializing` forever / "Connection to node 1 (localhost/127.0.0.1:9092) could not be established"](#24-kafka-ui-shows-status-initializing-forever--connection-to-node-1-localhost127009092-could-not-be-established)
  - [2.5 `slack_svc` log spams "Marking the coordinator dead" on startup](#25-slack_svc-log-spams-marking-the-coordinator-dead-on-startup)
- [3. ngrok / public tunnel](#3-ngrok--public-tunnel)
  - [3.1 `ERR_NGROK_4018: authentication failed`](#31-err_ngrok_4018-authentication-failed)
  - [3.2 I ran `ngrok http 80` (or any other port). What do I do?](#32-i-ran-ngrok-http-80-or-any-other-port-what-do-i-do)
  - [3.3 I pasted my ngrok authtoken in a shared chat. What now?](#33-i-pasted-my-ngrok-authtoken-in-a-shared-chat-what-now)
  - [3.4 The tunnel URL changes every time I restart](#34-the-tunnel-url-changes-every-time-i-restart)
  - [3.5 How do I kill every ngrok process? / How do I check what tunnel is currently up?](#35-how-do-i-kill-every-ngrok-process--how-do-i-check-what-tunnel-is-currently-up)
- [4. Slack app configuration](#4-slack-app-configuration)
  - [4.1 Messages post fine, but the *Claim* button shows "This app is not configured to handle interactive responses"](#41-messages-post-fine-but-the-claim-button-shows-this-app-is-not-configured-to-handle-interactive-responses)
  - [4.2 Slack admin: "Your URL didn't respond with the value of the challenge parameter"](#42-slack-admin-your-url-didnt-respond-with-the-value-of-the-challenge-parameter)
  - [4.3 The **Save Changes** button on *Event Subscriptions* is greyed out](#43-the-save-changes-button-on-event-subscriptions-is-greyed-out)
  - [4.4 Clicking *Claim* returns "This app responded with Status Code 404"](#44-clicking-claim-returns-this-app-responded-with-status-code-404)
  - [4.5 slack_svc log shows `slack.api_error` over and over with no reason](#45-slack_svc-log-shows-slackapi_error-over-and-over-with-no-reason)
  - [4.6 Bot posts but never reaches one of my channels — `not_in_channel`](#46-bot-posts-but-never-reaches-one-of-my-channels--not_in_channel)
  - [4.7 Where do I find `SLACK_SIGNING_SECRET`?](#47-where-do-i-find-slack_signing_secret)
  - [4.8 What is `SLACK_APP_CONFIG_TOKEN` and do I need it?](#48-what-is-slack_app_config_token-and-do-i-need-it)
- [5. Slack Integrations admin page](#5-slack-integrations-admin-page)
  - [5.1 `/app/slack-integrations` shows "Not Found" after I add a new backend route](#51-appslack-integrations-shows-not-found-after-i-add-a-new-backend-route)
  - [5.2 I wired two channels for the same event — only one receives the message](#52-i-wired-two-channels-for-the-same-event--only-one-receives-the-message)
- [6. Middleware / services](#6-middleware--services)
  - [6.1 I changed backend code — how do I make the running service pick it up?](#61-i-changed-backend-code--how-do-i-make-the-running-service-pick-it-up)
  - [6.2 `slack_svc` log is silent — is the Kafka consumer stuck?](#62-slack_svc-log-is-silent--is-the-kafka-consumer-stuck)
  - [6.3 How do I see which services are currently running?](#63-how-do-i-see-which-services-are-currently-running)
- [7. Admin + Support portals](#7-admin--support-portals)
  - [7.1 The admin / support apps show dummy data](#71-the-admin--support-apps-show-dummy-data)
  - [7.2 What credentials do I use to sign in?](#72-what-credentials-do-i-use-to-sign-in)
  - [7.3 Can employees sign up through the portal?](#73-can-employees-sign-up-through-the-portal)
  - [7.4 Sidebar navigation is unreadable — blue text on teal background](#74-sidebar-navigation-is-unreadable--blue-text-on-teal-background)
  - [7.5 Can I drill into a row on the admin / support list pages?](#75-can-i-drill-into-a-row-on-the-admin--support-list-pages)
- [8. Kafka UI](#8-kafka-ui)
  - [8.1 I see consumer lag = 0 but no Slack message arrived](#81-i-see-consumer-lag--0-but-no-slack-message-arrived)
  - [8.2 How do I see what's actually in `appointment.events`?](#82-how-do-i-see-whats-actually-in-appointmentevents)

---

## 1. First-run setup

### 1.1 How do I bring the whole stack up for the first time?

Once, per laptop:

```bash
# 1. Install ngrok + authtoken (one-time per machine)
npm run setup:local:ngrok

# 2. Create .env.local from the template and fill in real values
cp .env.local.example .env.local
$EDITOR .env.local
# Fill SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET, and optionally
# SLACK_APP_ID + SLACK_APP_CONFIG_TOKEN (see FAQ 4.8).

# 3. Bootstrap venv, portals, Docker, migrations
npm run setup:local:all
```

Every time after that:

```bash
npm run setup:local:docker:up    # postgres + kafka + kafka-ui + waits
npm run db:migrate:all
npm run local:middleware:start-all
npm run local:portals:start-all
npm run local:slack:tunnel:up    # only if you're testing the Slack Claim flow
```

Check status:

```bash
npm run local:status
```

### 1.2 What goes in `.env.local`?

`.env.local` is gitignored. Copy from `.env.local.example`, then fill in:

| Key | Required for | Where to get |
|---|---|---|
| `SLACK_BOT_TOKEN` | slack_svc posting to channels | https://api.slack.com/apps → your app → OAuth & Permissions → Bot User OAuth Token (`xoxb-...`) |
| `SLACK_SIGNING_SECRET` | Verifying inbound webhooks from Slack (Claim button, events) | https://api.slack.com/apps → your app → Basic Information → App Credentials → Signing Secret → Show |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka producer/consumer bootstrap | Leave as `localhost:9092` for local dev |
| `DATABASE_URL` | Every service's Postgres connection | Leave as `postgresql://care:care@localhost:5432/in_home_care_platform` for local dev |
| `SLACK_APP_ID` (optional) | Auto-pushing tunnel URL to Slack manifest | https://api.slack.com/apps → your app → Basic Information → App ID |
| `SLACK_APP_CONFIG_TOKEN` (optional) | Same — required only with `SLACK_APP_ID` | https://api.slack.com/apps → **Manage Distribution** → **App Configuration Tokens** → Generate Token (one-time, per workspace) |
| `IHCP_JWT_SECRET` (optional) | Override the local-dev JWT signing secret | Any string you pick |

Both `npm run local:middleware:start-all` and `DevOps/Local/member-middleware-start.sh` source this file automatically before launching uvicorn, so the env is visible to every Python process. You never have to `export` anything by hand.

### 1.3 How do I tear everything down cleanly (including DB state)?

```bash
npm run local:shutdown-all
```

This:

1. Kills every process in `/tmp/ihcp_*.pids` (middleware + portals).
2. Sweeps canonical ports (8001–8009 middleware, 3001–3003 portals) and SIGKILL's stragglers — catches vite processes you ran outside npm.
3. Tears the ngrok tunnel down if one was up.
4. Runs `docker compose down **-v**` on every stack so `kafka-data`, `postgres-data`, `mongodb-data`, `redis-data` are all wiped.
5. Prunes orphaned `kafka_*` / `postgres_*` / `in-home-*` volumes.

After `shutdown-all`, the next `setup:local:docker:up` boots with completely fresh volumes. This is the right command when you want a clean slate.

### 1.4 `stop-all` vs `shutdown-all` — which do I use?

| Command | Containers | Volumes | Use when |
|---|---|---|---|
| `npm run local:stop-all` | stopped/removed | **preserved** | Stop for the day, keep DB state |
| `npm run local:shutdown-all` | stopped/removed | **wiped** | Fresh start, no leftover state |

If in doubt: `stop-all` is non-destructive and safe. `shutdown-all` is destructive — DB rows, Slack integrations, seeded users, appointments are all gone after it runs (seeded users reappear on next `auth_svc` startup, but everything else has to be re-created).

---

## 2. Docker / Postgres / Kafka

### 2.1 `psycopg2.OperationalError: server closed the connection unexpectedly`

Classic Postgres startup race. `docker compose up -d` returns as soon as the container is *created*, not when `initdb` has finished, so any caller that runs alembic immediately after gets an unexpected half-initialized connection.

**Already fixed**: `setup:local:docker:up` now calls `DevOps/Local/wait-for-postgres.sh` which polls `pg_isready` inside the container (resolves in ~2 s on a fresh volume). `db-migrate-all.sh` and middleware startup run *after* the wait, so the race can't happen through the normal start path.

**If you still see it**, you either:
- Started middleware with `uvicorn` by hand before running `setup:local:docker:up`. Fix: `npm run local:shutdown-all && npm run setup:local:docker:up`.
- Are running the docker stack on a different machine where `pg_isready` isn't installed in the container. The apache/kafka and postgres:16 base images both ship it — unless you've replaced them, this shouldn't happen.

### 2.2 `docker compose down` keeps Postgres / Kafka data around

By design: `docker compose down` preserves named volumes. That's what `npm run local:stop-all` does under the hood, so a "stop for the day" keeps your DB state across restarts.

If you want to wipe volumes too, use `npm run local:shutdown-all` (see FAQ 1.4). That command inlines `docker compose down -v` for every stack plus a `docker volume rm` sweep for orphans.

### 2.3 Kafka container in a restart loop: `advertised.listeners cannot use the nonroutable meta-address 0.0.0.0`

Two bugs in the compose at once:

1. `KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093` — apache/kafka 3.9's storage-format step rejects the literal `0.0.0.0` anywhere in the listener config, not just in `advertised.listeners`.
2. `KAFKA_CONTROLLER_QUORUM_VOTERS: 1@kafka:9093` — referencing a hostname that didn't resolve inside the container.

**Already fixed**: `DevOps/Local/Kafka/docker-compose.yml` now uses empty-host syntax (`PLAINTEXT_HOST://:9092,CONTROLLER://:9093`), pins the controller voter to `1@localhost:9093`, adds `KAFKA_INTER_BROKER_LISTENER_NAME=PLAINTEXT_DOCKER`, and uses a dual-listener setup so both host Python clients and in-docker kafka-ui can reach the broker.

If you need to wipe a corrupted Kafka data volume:

```bash
docker compose -f DevOps/Local/Kafka/docker-compose.yml down -v
docker compose -f DevOps/Local/Kafka/docker-compose.yml up -d
```

### 2.4 `kafka-ui` shows `status: initializing` forever / "Connection to node 1 (localhost/127.0.0.1:9092) could not be established"

This is what happens when `kafka-ui` tries to bootstrap via a hostname that resolves to the wrong interface inside its own container. In particular: the broker advertises `localhost:9092`, and inside the kafka-ui container "localhost" is the container's own loopback, not the host — so the first metadata reply handed to kafka-ui is pointing at itself.

**Already fixed** with the same dual-listener change as FAQ 2.3:

- `PLAINTEXT_HOST://:9092 → advertised localhost:9092` — for host Python clients (slack_svc, appointment_svc).
- `PLAINTEXT_DOCKER://:29092 → advertised kafka:29092` — for containerised clients (kafka-ui).

Both kafka and kafka-ui are attached to the shared `in-home-care-network` Docker network, so `kafka:29092` resolves container-to-container.

`http://127.0.0.1:8088` is the UI. If it's still initializing after ~30 s, check `docker logs in-home-care-kafka-ui --tail 40`.

### 2.5 `slack_svc` log spams "Marking the coordinator dead" on startup

Transient — aiokafka retries internally while Kafka finishes creating the `__consumer_offsets` internal topic on first join. This *looks* like a permanent failure because my own `shared/kafka.py` INFO log lines (`kafka.consumer_started`, etc.) were previously dropped by Python's default WARNING root level, so the only output you saw was aiokafka's warning spam.

**Already fixed** in two places:

1. `slack_svc/main.py` now calls `logging.basicConfig(level=logging.INFO)` so diagnostic lines actually appear. After the fix, `tail /tmp/ihcp_slack_svc.log` shows `kafka.consumer_started topic=appointment.events group_id=slack_svc.appointments bootstrap=localhost:9092` as soon as the consumer connects cleanly.
2. `DevOps/Local/wait-for-kafka.sh` runs after `wait-for-postgres.sh` during docker stack startup so the broker is already ready by the time middleware tries to join. Removes most of the race window.

After both fixes, the "Marking the coordinator dead" lines either disappear or resolve within seconds, and `kafka.consumer_started` always follows.

---

## 3. ngrok / public tunnel

### 3.1 `ERR_NGROK_4018: authentication failed`

ngrok 3.x refuses to start without a free authtoken. One-time per laptop:

1. **Sign up** at https://dashboard.ngrok.com/signup (free)
2. **Copy your authtoken** from https://dashboard.ngrok.com/get-started/your-authtoken
3. **Install it:**
   ```bash
   ngrok config add-authtoken <YOUR_TOKEN>
   ```

Then `npm run local:slack:tunnel:up` will work. You can also run `npm run setup:local:ngrok` which walks you through both the brew install AND the token check (prints the 3-step instructions if the token is missing).

The tunnel script now detects `ERR_NGROK_4018` in the log on timeout and prints the same 3-step message automatically — so if you ever hit this again, the error message itself tells you what to do.

### 3.2 I ran `ngrok http 80` (or any other port). What do I do?

Kill the stray tunnel and use the npm script instead:

```bash
pkill -f 'ngrok http'
npm run local:slack:tunnel:up
```

slack_svc is on `:8009`, not `:80`. The npm script always targets the right port; running `ngrok http <n>` by hand is easy to get wrong. After FAQ 3.1's fix ngrok free tier **only allows one agent at a time**, so if you start one by hand AND the npm script starts another, they'll fight and the last one wins.

The `slack-tunnel.sh` script also now refuses to reuse an existing tunnel whose target isn't `http://127.0.0.1:8009` — if a stray tunnel is already up pointing at the wrong port, it errors out instead of silently reporting fake success.

### 3.3 I pasted my ngrok authtoken in a shared chat. What now?

Rotate it immediately:

1. Go to https://dashboard.ngrok.com/get-started/your-authtoken
2. Click **Reset Auth Token**
3. Copy the new one
4. Run `ngrok config add-authtoken <NEW_TOKEN>` locally
5. The old token is immediately invalid for any new session.

Also applies to `SLACK_BOT_TOKEN`, `SLACK_SIGNING_SECRET`, and `SLACK_APP_CONFIG_TOKEN`: never paste them in any chat, Slack message, or public gist. If you do, rotate them from the Slack app admin page: https://api.slack.com/apps/<APP_ID> → **Basic Information** → Regenerate / Revoke.

### 3.4 The tunnel URL changes every time I restart

ngrok **free tier does not pin subdomains.** Each `ngrok http 8009` session may assign a different random subdomain like `polite-tiger-flamingo.ngrok-free.dev`. That means:

- The URL you pasted into the Slack app admin goes stale.
- Old Block Kit messages in Slack channels link to the dead subdomain and return 404 on click (FAQ 4.4).

Two mitigations:

1. **Auto-push the new URL to Slack** on every tunnel restart. Set `SLACK_APP_ID` + `SLACK_APP_CONFIG_TOKEN` in `.env.local` (see FAQ 4.8). The tunnel script detects them and calls `apps.manifest.update` with the new URL — Slack admin stays in sync automatically. Old Block Kit messages still 404 though, since the subdomain in their `value` field is baked in at post time.
2. **Reserve a static domain** (free tier allows one). Go to https://dashboard.ngrok.com/cloud-edge/domains → Create Domain → pick a name like `yourname-dev.ngrok-free.app`. Then run ngrok with `--domain=<pinned-name>.ngrok-free.app`. The subdomain is stable forever; old Block Kit messages keep working across restarts. (The `slack-tunnel.sh` script does not yet pass `--domain` automatically — open an issue / PR if you want it.)

### 3.5 How do I kill every ngrok process? / How do I check what tunnel is currently up?

```bash
# Status from the npm script's perspective:
npm run local:slack:tunnel:status

# Inspector API directly (ground truth — shows what ngrok reports):
curl -s http://127.0.0.1:4040/api/tunnels | python3 -m json.tool

# Kill every ngrok process on this machine:
npm run local:slack:tunnel:down
# or as a nuclear option:
pkill -9 ngrok
```

`npm run local:shutdown-all` also tears the tunnel down as part of its global teardown.

---

## 4. Slack app configuration

### 4.1 Messages post fine, but the *Claim* button shows "This app is not configured to handle interactive responses"

Slack has the bot's posting token but no URL to POST back to when the button is clicked. You need to configure **Interactivity & Shortcuts → Request URL** in the Slack app admin:

1. Run `npm run local:slack:tunnel:up` to bring the tunnel up. It prints a public URL.
2. Paste `<public-url>/slack/interactivity` into https://api.slack.com/apps/<APP_ID>/interactive-messages.
3. Toggle **Interactivity** on and click **Save Changes**.
4. Slack does its URL verification handshake — slack_svc's `/slack/interactivity` route responds, Slack turns the indicator green.
5. Click Claim again — works.

If you set `SLACK_APP_ID` + `SLACK_APP_CONFIG_TOKEN` in `.env.local` (see FAQ 4.8), the tunnel script pushes this URL automatically every time it runs — you never have to open the admin page.

### 4.2 Slack admin: "Your URL didn't respond with the value of the challenge parameter"

Three possible root causes, in order of likelihood:

1. **`SLACK_SIGNING_SECRET` is missing or wrong in `.env.local`.** slack_svc verifies the signature Slack adds to the challenge request; if the secret doesn't match, slack_svc returns 401 and Slack reports this exact error. Quick diagnostic — from the repo root:
   ```bash
   SLACK_SIGNING_SECRET=$(grep '^SLACK_SIGNING_SECRET=' .env.local | cut -d= -f2-) python3 <<'PY'
   import os, time, hmac, hashlib, urllib.request, urllib.error
   sec = os.environ['SLACK_SIGNING_SECRET']
   ts = str(int(time.time()))
   body = '{"type":"url_verification","challenge":"x"}'
   sig = 'v0=' + hmac.new(sec.encode(), f'v0:{ts}:{body}'.encode(), hashlib.sha256).hexdigest()
   req = urllib.request.Request('http://127.0.0.1:8009/slack/events', data=body.encode(),
       headers={'Content-Type':'application/json','X-Slack-Request-Timestamp':ts,'X-Slack-Signature':sig}, method='POST')
   try:
       print('OK:', urllib.request.urlopen(req, timeout=5).read().decode())
   except urllib.error.HTTPError as e:
       print('FAIL:', e.code, e.read().decode())
   PY
   ```
   If this prints `OK: {"challenge":"x"}` then the secret in `.env.local` matches what's loaded in slack_svc — the remaining possibility is that the secret in `.env.local` doesn't match Slack's actual signing secret (someone copied the wrong value from the admin page — see FAQ 4.7).

2. **slack_svc was not restarted after editing `.env.local`.** The start script only sources `.env.local` at uvicorn launch time. If you edited it after starting middleware, kill slack_svc and restart:
   ```bash
   kill $(lsof -nP -iTCP:8009 -sTCP:LISTEN -t)
   npm run local:middleware:start-all
   ```

3. **The tunnel URL that Slack is POSTing to is not reaching your machine** (tunnel died — see FAQ 3.4 / FAQ 4.4).

### 4.3 The **Save Changes** button on *Event Subscriptions* is greyed out

Not a bug. Slack disables save until you also subscribe to at least one bot/user event type. **You don't need Event Subscriptions for the Claim button** — that button is an *interactivity* component, which is a separate page (*Interactivity & Shortcuts*). The Claim flow only needs that second page.

If you set `SLACK_APP_CONFIG_TOKEN` in `.env.local`, my tunnel script pushes both URLs via `apps.manifest.update` on every `tunnel:up` run, so you can ignore the Save button entirely — Slack already has the correct URLs server-side.

Verify the live state of the Slack app via the API:

```bash
python3 <<'PY'
import json, urllib.request
env = dict(l.strip().split('=',1) for l in open('.env.local') if '=' in l and not l.startswith('#'))
req = urllib.request.Request('https://slack.com/api/apps.manifest.export',
    data=json.dumps({'app_id': env['SLACK_APP_ID']}).encode(),
    headers={'Authorization': f"Bearer {env['SLACK_APP_CONFIG_TOKEN']}", 'Content-Type': 'application/json'},
    method='POST')
m = json.loads(urllib.request.urlopen(req, timeout=10).read())['manifest']
print('interactivity:', m['settings']['interactivity'])
print('events      :', m['settings'].get('event_subscriptions'))
PY
```

### 4.4 Clicking *Claim* returns "This app responded with Status Code 404"

The ngrok tunnel is down, but Slack still has the old URL saved. Slack POSTs to `https://<stale-subdomain>.ngrok-free.dev/slack/interactivity`, that subdomain no longer belongs to your ngrok account, and ngrok's edge returns 404.

Fix:

```bash
npm run local:slack:tunnel:up
```

If you set `SLACK_APP_CONFIG_TOKEN` in `.env.local`, the script auto-pushes the (possibly new) URL to Slack via `apps.manifest.update`. **New** Claim clicks will work immediately. *Old* Block Kit messages sent before the tunnel died may still have a stale subdomain embedded in their `value` and continue to 404 — create a new appointment to get a fresh card with the new URL, or see FAQ 3.4 for the static-domain fix that prevents this entirely.

### 4.5 slack_svc log shows `slack.api_error` over and over with no reason

This was a logging bug. `shared/slack.py` used `log.warning('...', extra={...})`, but Python's default logging formatter silently drops the `extra` dict — so every Slack API error showed up as a bare `slack.api_error` line with no error code.

**Already fixed**: the log format now inlines method + error code directly into the message string, with short actionable hints for the four most common error codes:

```
slack.api_error method=chat.postMessage error=not_in_channel (invite the bot to the channel: /invite @your_bot)
slack.api_error method=chat.postMessage error=channel_not_found (channel id/name does not exist or bot lacks visibility)
slack.api_error method=chat.postMessage error=invalid_auth (SLACK_BOT_TOKEN is invalid or revoked)
slack.api_error method=chat.postMessage error=missing_scope (bot token is missing required scope: needed=..., provided=...)
```

If you see one of these lines, the fix is usually obvious from the hint. If the error code is something else, look it up at https://api.slack.com/methods/<method-name>.

### 4.6 Bot posts but never reaches one of my channels — `not_in_channel`

The bot user isn't a member of that channel. Two ways to fix:

1. **Easier, from the admin portal**: go to `http://127.0.0.1:3002/app/slack-integrations`. Any channel the bot is *not* in shows an **Invite bot** button — click it. Under the hood it calls `conversations.invite` with the bot's own user id.
2. **From a Slack client**: open the channel and type `/invite @inhomecare_bot`.

After either, slack_svc's next post attempt will succeed. If it was previously in a redelivery loop (Kafka re-delivering the same failed message), the next poll cycle after the invite picks it up automatically — no restart needed.

### 4.7 Where do I find `SLACK_SIGNING_SECRET`?

Go to https://api.slack.com/apps → click your app (`inhomecare_bot` or whatever you named it) → **Basic Information** in the left sidebar → scroll to the **App Credentials** section.

There are five values on that page — **only "Signing Secret" is the right one**:

| Label on the page | This is NOT your signing secret |
|---|---|
| App ID | → goes in `SLACK_APP_ID` |
| Client ID | not used by this project |
| Client Secret | not used by this project |
| **Signing Secret** | → **this is your `SLACK_SIGNING_SECRET`** |
| Verification Token | deprecated by Slack, do not use |

Click **Show** next to "Signing Secret", copy the 32-character hex string (no quotes, no leading/trailing whitespace), and paste it as the value of `SLACK_SIGNING_SECRET=` in `.env.local`. Restart slack_svc (`kill $(lsof -nP -iTCP:8009 -sTCP:LISTEN -t)` + `npm run local:middleware:start-all`).

### 4.8 What is `SLACK_APP_CONFIG_TOKEN` and do I need it?

**Short answer**: optional, but if you set it, the tunnel URL is auto-pushed to Slack on every `tunnel:up` and you never touch the Slack admin UI again.

**Long answer**: Slack has a separate API (`apps.manifest.export` / `apps.manifest.update`) for programmatically reading and writing your app's manifest — which includes the Interactivity and Event Subscriptions request URLs. The API requires a workspace-scoped **App Configuration Token** (different from the bot token, different from client secret, different from verification token).

To create one:

1. Go to https://api.slack.com/apps
2. In the top navigation click **Your Apps**, then click your app
3. In the left sidebar click **Manage Distribution**
4. Scroll to **App Configuration Tokens**
5. Click **Generate Token** — one per workspace

Copy the token (`xoxe.xoxp-...`) and put it in `.env.local`:

```
SLACK_APP_ID=A0AS7Q08LEN
SLACK_APP_CONFIG_TOKEN=xoxe.xoxp-...
```

Now every `npm run local:slack:tunnel:up` will:

1. Start ngrok and wait for the public URL.
2. Call `apps.manifest.export` to fetch the current manifest.
3. Patch `interactivity.request_url` and `event_subscriptions.request_url` with the new tunnel URL.
4. Call `apps.manifest.update` to write it back.
5. Print `Slack app manifest updated successfully.`

No browser, no copy-paste. The Slack admin reflects the new URL immediately.

Without these two env vars, the tunnel script still works — it just prints the URL and expects you to paste it into the admin pages yourself.

---

## 5. Slack Integrations admin page

### 5.1 `/app/slack-integrations` shows "Not Found" after I add a new backend route

uvicorn doesn't auto-reload by default, so api_gateway is still running the binary from whenever you last started middleware. It hasn't re-imported the Python module with your new routes.

Fix:

```bash
# Option A: restart the whole middleware stack
npm run local:shutdown-all && npm run local:middleware:start-all

# Option B: kill just api_gateway and let local:middleware:start-all
# restart it next time
kill $(lsof -nP -iTCP:8001 -sTCP:LISTEN -t)
npm run local:middleware:start-all
```

After the restart, check what routes are now registered:

```bash
curl -fs http://127.0.0.1:8001/openapi.json | python3 -c "import sys,json; [print(p) for p in sorted(json.load(sys.stdin)['paths'])]" | grep /api/admin
```

You should see every admin route including `/api/admin/slack/channels`, `/api/admin/slack/integrations`, etc.

### 5.2 I wired two channels for the same event — only one receives the message

This used to be a real bug — my original `SlackIntegrationStore.find_enabled_for_event` used `ORDER BY id ASC LIMIT 1`, which silently dropped every integration row past the first. Fan-out was the obvious user mental model ("every wired channel receives the message"), and that's what actually happens now.

**Already fixed**: `list_enabled_for_event` returns the full enabled set, the slack_svc consumer iterates and posts to every target, and a new `appointment_slack_posts` table deduplicates per `(appointment_id, slack_channel_id)` so a Kafka redelivery never re-posts to a channel it already hit.

If you wire two channels on the Slack Integrations page, both will receive the next `appointment.booked` event. The admin page also shows a blue **"Fan-out active"** banner when any event type is mapped to 2+ channels so you can tell at a glance.

---

## 6. Middleware / services

### 6.1 I changed backend code — how do I make the running service pick it up?

uvicorn doesn't auto-reload. Restart the single service or the whole middleware stack:

```bash
# Just one service (example: api_gateway)
kill $(lsof -nP -iTCP:8001 -sTCP:LISTEN -t)
npm run local:middleware:start-all

# Or nuke and restart everything
npm run local:shutdown-all
npm run setup:local:docker:up
npm run db:migrate:all
npm run local:middleware:start-all
```

If you want hot-reload during development, run a single service with `--reload` directly:

```bash
$HOME/runtime_data/python_venvs/In-Home-Care-Platform/bin/uvicorn \
  api_gateway.main:app \
  --host 127.0.0.1 --port 8001 \
  --app-dir middleware/Microservices/api_gateway/src \
  --reload
```

But don't mix `--reload` with the pid-file tracking in `local:middleware:start-all` — stop that first so the two don't race.

### 6.2 `slack_svc` log is silent — is the Kafka consumer stuck?

Probably not. See FAQ 2.5. Python's default root logger level was WARNING which dropped every INFO line from my consumer code. After the fix (`logging.basicConfig(level=logging.INFO)` in `slack_svc/main.py`), the log shows:

```
INFO shared.kafka        kafka.consumer_started topic=appointment.events group_id=slack_svc.appointments bootstrap=localhost:9092
INFO slack_svc.consumer  slack_svc.fanout_done appointment_id=N posted=M targets=M already=0
INFO slack_svc.consumer  slack_svc.appointment_gone   (if the appointment was deleted between produce and consume)
INFO slack_svc.consumer  slack_svc.dedup_skip appointment_id=N channel=C... (on Kafka redelivery to an already-posted channel)
WARNING aiokafka.consumer.group_coordinator Marking the coordinator dead (node 1) for group slack_svc.appointments.  (transient, usually clears in seconds)
```

If you still see no lines after INFO was enabled, the consumer really isn't running. Check:

1. `lsof -nP -iTCP:8009 -sTCP:LISTEN` — is slack_svc even up?
2. `docker ps` — is `in-home-care-kafka` running?
3. `npm run local:status` — one-line summary of everything.

### 6.3 How do I see which services are currently running?

```bash
npm run local:status
```

Probes every canonical port:

```
=== Docker ===
in-home-care-kafka       Up 2 minutes (healthy)   0.0.0.0:9092->9092/tcp
in-home-care-kafka-ui    Up 2 minutes             0.0.0.0:8088->8080/tcp
in-home-care-postgres    Up 2 minutes (healthy)   0.0.0.0:5432->5432/tcp

=== Middleware (port healthz probe) ===
  [running] api_gateway                :8001
  [running] auth_svc                   :8002
  [running] member_svc                 :8003
  [running] appointment_svc            :8004
  [running] visit_management_svc       :8005
  ...
  [running] slack_svc                  :8009

=== Portals (port probe) ===
  [running] member_portal              :3001
  [running] care_admin_portal          :3002
  [running] customer_support_app       :3003

=== Tooling (port probe) ===
  [running] kafka-ui                   :8088
```

---

## 7. Admin + Support portals

### 7.1 The admin / support apps show dummy data

They used to — the first draft was a single-page mock with hardcoded `stats = [...]` / `cases = [...]` arrays and no routing, no API client, no auth.

**Already fixed** in `feat(rbac): seed internal users + sign-in to admin and support apps`. Both apps now have:

- `lib/api.ts` → `fetch` against api_gateway
- `context/AuthContext.tsx` → JWT in localStorage, `/api/auth/me` refresh
- Real routes under react-router-dom (`/signin`, `/app/...`)
- Sign-in page (dev credentials pre-filled)
- Role-gated backends:
  - `/api/admin/*` — admin role only
  - `/api/support/*` — support + admin
- Detail views on every list (added in `feat(portals): add detail views across admin and support apps`)

If you're seeing dummy data, you're on an old commit. `git pull`.

### 7.2 What credentials do I use to sign in?

All seeded by `auth_svc/seed.py` on every service startup (idempotent — existing rows are left alone so you can rotate passwords manually without being overwritten):

| Role | Email | Password |
|---|---|---|
| admin | `admin01@inhomecare.local` | `Admin@123` |
| support | `supportuser01@inhomecare.local` | `Support@123` |
| field_officer | `fieldofficer01@inhomecare.local` | `Field@123` |
| care_planner | `careplanner01@inhomecare.local` | `Plan@123` |
| auditor | `auditor01@inhomecare.local` | `Audit@123` |

The dev credentials are intentionally weak (typable). In non-local environments, override them via the `IHCP_INTERNAL_USERS_SEED_OVERRIDE` env var — see `auth_svc/seed.py` for the expected JSON shape.

The sign-in forms on both admin and support apps **pre-fill** with the appropriate credential so dev flow is two clicks:

- `http://127.0.0.1:3002/signin` — pre-filled with `admin01` / `Admin@123`
- `http://127.0.0.1:3003/#/signin` — pre-filled with `supportuser01` / `Support@123`

### 7.3 Can employees sign up through the portal?

No. Internal staff (admin, support, field_officer, care_planner, auditor) are **seeded** — sign-up is intentionally not exposed for those accounts. `/api/auth/signup` is still there but it hardcodes role `member`, and member_portal is the only portal that surfaces it.

If you need to add another internal user:

1. Edit `INTERNAL_USERS` in `middleware/Microservices/auth_svc/src/auth_svc/seed.py`.
2. Restart auth_svc: `kill $(lsof -nP -iTCP:8002 -sTCP:LISTEN -t) && npm run local:middleware:start-all`.

Or for a one-off, insert directly in the DB:

```bash
psql -h localhost -U care -d in_home_care_platform -c \
  "INSERT INTO auth_schema.users(email, hashed_password, role, is_active, created_at)
   VALUES ('newperson@inhomecare.local', '<bcrypt-hashed-value>', 'admin', TRUE, now());"
```

(Hash a password with `shared.auth.hash_password` in a Python shell.)

### 7.4 Sidebar navigation is unreadable — blue text on teal background

Two overlapping CSS issues caused this:

1. `react-router-dom`'s `<NavLink>` renders an `<a>` tag, and the browser user-agent stylesheet sets `a { color: -webkit-link }` (blue) which wins over inherited `text-white` from the parent `<aside>`.
2. `portals/web_apps/care_admin_portal/src/index.css` and `portals/desktop_app/customer_support_app/src/index.css` had a global `a { color: var(--color-info); }` rule (same `#1976D2`) that beat any Tailwind class on equal specificity.

**Already fixed** in `fix(portals): make NavLinks readable on dark sidebars/headers`:

1. Every `<NavLink>` in `AppShell.tsx` gets an inline `style={{ color: '#ffffff', textDecoration: 'none' }}` — inline wins over everything.
2. The global `a` rule in both `index.css` files is now `a { color: inherit; text-decoration: none; }` (matching `member_portal`'s convention). Anchors that genuinely want the blue link colour can opt in per element.

If you see blue nav text again, `git pull` and hard-refresh the browser.

### 7.5 Can I drill into a row on the admin / support list pages?

Yes — since `feat(portals): add detail views across admin and support apps`. Click any row in:

- **admin**: Appointments, Members, Visits, Slack Claims, Dashboard (recent appointments table)
- **support**: Cases, Members, Appointments, Visits

Each list row navigates to `/app/<entity>/:id` and renders a detail page with every field, badges for status/priority, and cross-links between related entities (e.g. Visit detail has clickable Member and Appointment links).

---

## 8. Kafka UI

### 8.1 I see consumer lag = 0 but no Slack message arrived

Lag = 0 means the consumer *read* the message, not that the handler *succeeded*. If the handler returns success (returns True) the offset commits even on a terminal skip (appointment deleted, already posted elsewhere, etc.).

To figure out what actually happened, read the slack_svc log for the appointment id:

```bash
grep 'appointment_id=<N>' /tmp/ihcp_slack_svc.log
```

You'll see one of:

- `slack_svc.fanout_done appointment_id=N posted=M targets=M already=0` — happy path, M channels received the message
- `slack_svc.appointment_gone appointment_id=N` — the appointment was deleted before the consumer got to it (safe skip)
- `slack_svc.appointment_cancelled appointment_id=N` — appointment status is `cancelled` (safe skip)
- `slack_svc.dedup_skip appointment_id=N channel=C...` — this appointment has already been posted to this channel, skipping redelivery
- `slack_svc.post_failed appointment_id=N channel=C... slack_error=<code>` — the actual Slack API failure (see FAQ 4.5 for decoding error codes)

The most common cause of "lag = 0 but no message" is actually: you have **no enabled integration row** for the event type, AND the env-var default channel (`SLACK_APPOINTMENT_REQUESTS_CHANNEL`) points at a channel the bot isn't in (FAQ 4.6). Both fail silently from the lag's perspective.

### 8.2 How do I see what's actually in `appointment.events`?

Open `http://127.0.0.1:8088` (kafka-ui) → **Topics** → `appointment.events` → **Messages**. You'll see every published event in reverse chronological order with the JSON payload exposed. Click a row to see the full payload plus headers.

Or from the CLI inside the container:

```bash
docker exec -it in-home-care-kafka /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic appointment.events \
  --from-beginning
```

Ctrl-C when done. Each line is one event: `{"event_type": "appointment.booked", "appointment_id": N, "occurred_at": "..."}`.

To publish a test event manually (useful for exercising slack_svc without going through the member portal):

```bash
docker exec in-home-care-kafka bash -c "echo '{\"event_type\":\"appointment.booked\",\"appointment_id\":999,\"occurred_at\":\"2026-04-11T21:00:00Z\"}' | /opt/kafka/bin/kafka-console-producer.sh --bootstrap-server localhost:9092 --topic appointment.events"
```

Then watch `tail -f /tmp/ihcp_slack_svc.log` for the consumer's reaction.

---

*Last updated: 2026-04-11 — captures every issue encountered while bringing Slack fan-out + Claim button + RBAC admin portal live end-to-end on a fresh MacBook.*
