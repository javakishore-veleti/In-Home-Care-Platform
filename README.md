# In-Home-Care-Platform

![Domain](https://img.shields.io/badge/Domain-In--Home%20Care-blue)
![Architecture](https://img.shields.io/badge/Architecture-Microservices-6A5ACD)
![Backend](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white)
![Frontend](https://img.shields.io/badge/Web-React-61DAFB?logo=react&logoColor=black)
![Mobile](https://img.shields.io/badge/Mobile-React%20Native-20232A?logo=react&logoColor=61DAFB)
![Desktop](https://img.shields.io/badge/Desktop-Electron-47848F?logo=electron&logoColor=white)
![Events](https://img.shields.io/badge/Event%20Streaming-Kafka-231F20?logo=apachekafka&logoColor=white)
![AI](https://img.shields.io/badge/AI-LangGraph-4B0082)
![LLM](https://img.shields.io/badge/LLM-RAG%20%2B%20Slack%20Copilot-7C3AED)
![Gateway](https://img.shields.io/badge/Gateway-MCP%20%2F%20ADK-0F766E)
![Database](https://img.shields.io/badge/Database-MongoDB%20%2B%20Postgres-336791)
![Cache](https://img.shields.io/badge/Cache-Redis-DC382D?logo=redis&logoColor=white)
![VectorDB](https://img.shields.io/badge/VectorDB-Qdrant%20%7C%20Weaviate%20%7C%20Chroma-FF6B6B)
![Docs](https://img.shields.io/badge/Docs-Architecture%20Draw.io-orange)
![Status](https://img.shields.io/badge/Status-Active%20Development-brightgreen)

## Table of contents

- [Business domain](#business-domain)
- [Repository layout](#repository-layout)
- [Architecture](#architecture-mapped-to-docsdesignarchitecturedrawio)
  - [Tab 1 — System Overview](#tab-1--system-overview)
  - [Tab 2 — Book Appointment Flow](#tab-2--book-appointment-flow)
  - [Tab 3 — Sign Up + Sign In](#tab-3--sign-up--sign-in)
  - [Tab 4 — Visit Listing + Lifecycle](#tab-4--visit-listing--lifecycle)
  - [Tab 5 — Microservice Map](#tab-5--microservice-map)
  - [Tab 6 — LangGraph Agentic Flows](#tab-6--langgraph-agentic-flows)
  - [Tab 7 — Data Model](#tab-7--data-model)
- [Tech stack](#tech-stack)
- [Getting started — npm commands for everything](#getting-started--npm-commands-for-everything)
  - [First-time setup (run once after clone)](#first-time-setup-run-once-after-clone)
  - [Daily workflow — start / stop / status](#daily-workflow--start--stop--status)
  - [Portal commands](#portal-commands-each-does-npm-install-before-devbuild)
  - [Middleware commands](#middleware-commands)
  - [Docker infrastructure commands](#docker-infrastructure-commands)
  - [Database migrations](#database-migrations)
  - [Test + lint](#test--lint)
  - [Teardown (nuclear option)](#teardown-nuclear-option)
  - [Full npm script reference](#full-npm-script-reference)
- [Slack integration — setup + credentials](#slack-integration--setup--credentials)
  - [Channels](#channels)
  - [Step 1 — Create a Slack app](#step-1--create-a-slack-app)
  - [Step 2 — Add bot token scopes](#step-2--add-bot-token-scopes)
  - [Step 3 — Install to workspace](#step-3--install-to-workspace)
  - [Step 4 — Export the token](#step-4--export-the-token)
  - [Step 5 — Create the channels](#step-5--create-the-channels)
  - [Check channel status](#check-channel-status)
  - [Tear down channels](#tear-down-channels)
  - [Adding or renaming channels](#adding-or-renaming-channels)
- [Status](#status)

---

A full-stack in-home healthcare delivery platform. Members book
appointments, field staff conduct visits with a mobile app, customer
support handles cases from a desktop app, and admin staff manage
operations from a React portal. The middleware layer runs FastAPI
microservices, a FastMCP/ADK gateway, Kafka event streaming, and
LangGraph agentic flows backed by VectorDB + LLM. Slack channel
integration gives all three personas an AI-assisted back-office
copilot.

This is a **monorepo** — each folder is conceptually a separate service
or app, sharing infrastructure and documentation at the root.

## Business domain

In-home care delivery (home health, personal care, companion care).
A care organization dispatches field staff to members' homes for
scheduled visits. The platform handles:

1. **Member self-service** — book an appointment, view upcoming and
   past visits, manage profile.
2. **Field staff mobile** — receive assignments, record visit notes,
   capture intake forms, flag follow-ups.
3. **Customer support desktop** — handle inbound calls and chats,
   look up member/visit records, escalate issues.
4. **Admin portal** — manage staff rosters, service areas, scheduling
   rules, view dashboards.
5. **AI-assisted back-office** — Slack channels for each persona
   where a LangGraph agent answers grounded questions from policies,
   past visits, and resolved tickets.

## Repository layout

```
In-Home-Care-Platform/
│
├── middleware/
│   ├── Microservices/
│   │   ├── api_gateway/                 # FastAPI gateway — routes, auth, rate limiting
│   │   ├── auth_svc/                    # Sign up / sign in / token management
│   │   ├── member_svc/                  # Member (patient) profile CRUD
│   │   ├── appointment_svc/             # Book / cancel / reschedule appointments
│   │   ├── visit_management_svc/        # Visit lifecycle, listing, status
│   │   ├── visit_ingest_svc/            # Field data ingest from mobile app
│   │   ├── document_intelligence_svc/   # GCP Document AI — OCR, form extraction
│   │   └── mcp_gateway/                 # FastMCP + ADK gateway for LLM tool access
│   │
│   └── AgenticFlows/
│       ├── visit_intelligence_flow/     # LangGraph: visit scoring + follow-up detection
│       ├── slack_channel_responder_flow/ # LangGraph: Slack Q&A with RAG
│       └── document_author_flow/        # LangGraph: draft visit summaries from docs
│
├── portals/
│   ├── web_apps/
│   │   ├── member_portal/               # React — book appointment, view visits
│   │   └── care_admin_portal/           # React — admin dashboard, staff mgmt
│   ├── mobile_app/
│   │   └── field_staff_app/             # React Native / Flutter — visit recording
│   └── desktop_app/
│       └── customer_support_app/        # Electron / desktop — case handling
│
├── DevOps/Local/
│   ├── MongoDB/ Kafka/ Postgres/ Redis/
│   ├── VectorDBs/{qdrant,weaviate,chroma,milvus,pgvector}/
│   ├── Observability/{Prometheus,Grafana,Kibana}/
│
├── Docs/Design/
│   └── architecture.drawio              # 7-tab architecture diagram
│
├── README.md                            # ← you are here
└── README_Development_Plan.md
```

Each folder under `middleware/Microservices/` and `middleware/AgenticFlows/`
is a standalone Python service with its own `pyproject.toml`, `src/`, and
`tests/`. Portals are standalone frontend projects. Infrastructure holds
Docker Compose stacks for local dev.

## Architecture (mapped to `Docs/Design/architecture.drawio`)

### Tab 1 — System Overview

Three personas enter through three Slack channels and three apps:

| Persona | App | Slack channel |
|---|---|---|
| Field staff | Mobile app | `#field-ops` |
| Customer support | Desktop app | `#customer-support` |
| Admin staff | React admin portal | `#care-admin` |

All apps talk to the **API gateway** (FastAPI). The gateway routes to
microservices. Events flow through **Kafka**. The **MCP gateway**
(FastMCP + ADK) exposes microservice tools to LLM clients. **LangGraph
agentic flows** consume from Slack channels, query **VectorDB** +
invoke microservices + call the **LLM**, and post threaded replies.
**MongoDB** is the central data store.

### Tab 2 — Book Appointment Flow

Member portal → API gateway → `appointment_svc` → MongoDB (appointments
collection) → Kafka event `appointment.booked` → `visit_management_svc`
creates a pending visit → notification to assigned field staff via
mobile app push.

### Tab 3 — Sign Up + Sign In

Member portal / mobile app / desktop app → API gateway → `auth_svc` →
MongoDB (users collection). JWT issued on sign-in, verified at the
gateway on every subsequent call. Role-based: `member`, `field_staff`,
`support`, `admin`.

### Tab 4 — Visit Listing + Lifecycle

Member portal shows upcoming and past visits. Field staff mobile app
shows today's assignments. Both read from `visit_management_svc` →
MongoDB (visits collection). Field staff mobile app posts visit notes
via `visit_ingest_svc` → `document_intelligence_svc` (GCP Doc AI) →
MongoDB (visit_documents, extracted_fields).

### Tab 5 — Microservice Map

Eight services, their responsibilities, and which collections they own:

| Service | Owns | Talks to |
|---|---|---|
| `api_gateway` | — (routes only) | all services |
| `auth_svc` | users, sessions | — |
| `member_svc` | members | — |
| `appointment_svc` | appointments | Kafka, visit_management_svc |
| `visit_management_svc` | visits | member_svc |
| `visit_ingest_svc` | visit_documents | document_intelligence_svc |
| `document_intelligence_svc` | extracted_fields | GCP Document AI |
| `mcp_gateway` | — (tools only) | all services, VectorDB, LLM |

### Tab 6 — LangGraph Agentic Flows

Three flows:

1. **Slack Channel Responder** — watches configured channels, classifies
   the message, retrieves from VectorDB (policies + tickets + past
   threads), calls LLM, replies in-thread, logs the answer.
2. **Visit Intelligence** — triggered on visit completion, scores the
   visit data, detects care gaps and follow-up tasks, writes
   dispositions.
3. **Document Author** — drafts visit summaries from extracted fields +
   past visit context, presents for staff review.

### Tab 7 — Data Model

MongoDB collections grouped by owning service:

- `auth_svc`: users, sessions
- `member_svc`: members
- `appointment_svc`: appointments
- `visit_management_svc`: visits
- `visit_ingest_svc`: visit_documents
- `document_intelligence_svc`: extracted_fields
- `mcp_gateway`: — (reads across all)
- `slack_channel_responder_flow`: messages, threads, answer_logs
- `visit_intelligence_flow`: visit_scores, dispositions
- VectorDB: policies, runbooks, tickets, slack_threads

## Tech stack

| Layer | Choice |
|---|---|
| API gateway + microservices | FastAPI (Python) |
| Auth | JWT + role-based (member / field_staff / support / admin) |
| MCP gateway | FastMCP + Google ADK (LlmAgent + Runner) |
| Agentic workflows | LangGraph (state machine with conditional edges) |
| LLM | Google ADK / OpenAI / Anthropic — pluggable via LlmClient Protocol |
| Vector DB | Qdrant default; pluggable via VectorClient Protocol |
| Storage | MongoDB |
| Events | Kafka (or in-memory bus for dev) |
| Document AI | GCP Document AI |
| Web portals | React |
| Mobile app | React Native or Flutter |
| Desktop app | Electron or Tauri |
| Logging | structlog with PII-aware processor |
| Tests | Pytest + mongomock + FakeSlackClient + FakeLlmClient |
| CI | GitHub Actions |
| Deploy | GCP Cloud Run + Kubernetes manifests |

## Getting started — npm commands for everything

Every operation is an `npm run` script. No raw `cd`, no manual
`pip install`, no manual `npm install` inside portal folders.

### First-time setup (run once after clone)

```bash
# 1. Create conda venv + install all Python deps + install all portal
#    node_modules + bring up all docker stacks
npm run setup:local:all
```

This runs four steps in order:

| Step | What it does |
|---|---|
| `setup:local:venv:create` | `conda create -y -p ~/runtime_data/python_venvs/In-Home-Care-Platform python=3.13` |
| `setup:local:venv:install` | `pip install -r requirements.txt` (all middleware + agentic flow deps) |
| `setup:local:portals:install` | `npm install` inside member_portal, care_admin_portal, customer_support_app |
| `setup:local:docker:up` | Docker Compose up for MongoDB, Kafka, Postgres, Redis, VectorDBs, Prometheus, Grafana, Kibana, Airflow — all on shared network `in-home-care-network` |

To activate the conda venv in your shell (for running Python directly):

```bash
npm run setup:local:venv:activate
# then copy-paste the printed command into your shell
```

### Daily workflow — start / stop / status

```bash
# Start everything (docker + 8 middleware services + web portals)
npm run local:start-all

# Or start layers individually:
npm run setup:local:docker:up         # docker stacks only
npm run local:middleware:start-all    # uvicorn all 8 services (ports 8001-8008)
npm run local:portals:start-all       # vite dev for web portals in parallel

# Check what's running
npm run local:status-all

# Stop everything
npm run local:stop-all
```

### Portal commands (each does npm install before dev/build)

**Member Portal** (React, http://localhost:3001):

```bash
npm run setup:local:portal:member     # npm install
npm run local:portal:member:dev       # vite dev server on :3001
npm run local:portal:member:build     # tsc + vite build
```

**Care Admin Portal** (React, http://localhost:3002):

```bash
npm run setup:local:portal:admin      # npm install
npm run local:portal:admin:dev        # vite dev server on :3002
npm run local:portal:admin:build      # tsc + vite build
```

**Customer Support Desktop App** (Electron + React, http://localhost:3003):

```bash
npm run setup:local:portal:desktop    # npm install
npm run local:portal:desktop:dev      # vite dev server on :3003
npm run local:portal:desktop:electron # launch Electron window (loads :3003)
npm run local:portal:desktop:build    # tsc + vite build (for packaged Electron)
```

**Field Staff Mobile App** (React Native / Expo):

```bash
npm run setup:local:portal:mobile     # npm install
npm run local:portal:mobile:start     # expo start (scan QR with Expo Go)
npm run local:portal:mobile:ios       # expo start --ios
npm run local:portal:mobile:android   # expo start --android
npm run local:portal:mobile:web       # expo start --web
```

### Middleware commands

```bash
npm run local:middleware:start-all    # uvicorn all 8 services (ports 8001-8008)
npm run local:middleware:stop-all     # kill all middleware PIDs
npm run local:middleware:status-all   # check PID liveness
```

### Docker infrastructure commands

```bash
npm run setup:local:docker:up         # bring up all stacks
npm run setup:local:docker:down       # tear down all stacks
npm run setup:local:docker:status     # show running containers
```

### Database migrations

Migrations run **automatically** — you never need to run them by hand:

- **Local:** `npm run setup:local:all` and `npm run local:start-all`
  both chain `npm run db:migrate:all` before starting services.
- **AWS / container:** every microservice's `create_app()` calls
  `run_migrations()` from `middleware/shared/auto_migrate.py` on
  startup — runs `alembic upgrade head` (idempotent, skips if at
  head already).

If you need to run manually or check status:

```bash
npm run db:migrate:all                # run all 7 service migrations
npm run db:status                     # show current revision per schema
```

Each service owns its own Postgres **schema** inside the shared
`in_home_care_platform` database (no table collisions):

| Service | Schema | Tables |
|---|---|---|
| `auth_svc` | `auth_schema` | users, sessions |
| `member_svc` | `member_schema` | members |
| `appointment_svc` | `appointment_schema` | appointments |
| `visit_management_svc` | `visit_schema` | visits |
| `visit_ingest_svc` | `visit_ingest_schema` | visit_documents |
| `document_intelligence_svc` | `doc_intel_schema` | extracted_fields |
| `collection_ingest_svc` | `collection_schema` | collections, ingest_jobs |

### Test + lint

```bash
npm test                              # pytest -q across all middleware
npm run test:middleware                # pytest middleware/ only
npm run lint                          # ruff check .
```

### Teardown (nuclear option)

```bash
npm run teardown:local:all            # stop everything + delete the conda venv
```

### Full npm script reference

| Script | Purpose |
|---|---|
| `setup:local:all` | First-time: venv + pip + portal npm install + docker up |
| `setup:local:venv:create` | Create conda env at `~/runtime_data/python_venvs/In-Home-Care-Platform` |
| `setup:local:venv:install` | `pip install -r requirements.txt` into the conda venv |
| `setup:local:venv:activate` | Print the `conda activate` command |
| `setup:local:venv:deactivate` | Print `conda deactivate` |
| `setup:local:venv:destroy` | Delete the conda venv |
| `setup:local:portals:install` | `npm install` in all 3 web/desktop portals |
| `setup:local:portal:member` | `npm install` in member_portal |
| `setup:local:portal:admin` | `npm install` in care_admin_portal |
| `setup:local:portal:desktop` | `npm install` in customer_support_app |
| `setup:local:portal:mobile` | `npm install` in field_staff_app |
| `setup:local:docker:up` | Docker Compose up all stacks |
| `setup:local:docker:down` | Docker Compose down all stacks |
| `setup:local:docker:status` | Docker Compose ps all stacks |
| `local:middleware:start-all` | Uvicorn all 8 services (8001-8008) |
| `local:middleware:stop-all` | Kill middleware PIDs |
| `local:middleware:status-all` | Check middleware PID liveness |
| `local:portals:start-all` | Vite dev all web portals in parallel |
| `local:portal:member:dev` | Member portal on :3001 |
| `local:portal:member:build` | Build member portal |
| `local:portal:admin:dev` | Admin portal on :3002 |
| `local:portal:admin:build` | Build admin portal |
| `local:portal:desktop:dev` | Desktop app Vite on :3003 |
| `local:portal:desktop:electron` | Launch Electron window |
| `local:portal:desktop:build` | Build desktop app |
| `local:portal:mobile:start` | Expo start |
| `local:portal:mobile:ios` | Expo iOS |
| `local:portal:mobile:android` | Expo Android |
| `local:portal:mobile:web` | Expo web |
| `local:portals:stop-all` | Kill portal PIDs |
| `local:portals:status-all` | Check portal PID liveness |
| `local:start-all` | Docker + middleware + portals |
| `local:stop-all` | Reverse of above |
| `local:status-all` | Check all layers |
| `test` | `pytest -q` via conda venv |
| `test:middleware` | `pytest middleware/` only |
| `lint` | `ruff check .` |
| `teardown:local:all` | Stop all + destroy venv |
| `setup:slack:channels` | Create all 4 Slack channels |
| `status:slack:channels` | Check Slack channel status |
| `teardown:slack:channels` | Archive all 4 Slack channels |

## Slack integration — setup + credentials

The platform uses four Slack channels for AI-assisted back-office
support. The LangGraph `slack_channel_responder_flow` watches these
channels, answers questions with grounded context, and replies
in-thread.

### Channels

| Channel | Persona |
|---|---|
| `#in-home-help-field-officers` | Field staff |
| `#in-home-help-customer-support` | Customer support agents |
| `#in-home-help-product-owners` | Product owners |
| `#in-home-help-customers` | Members / patients |

### Step 1 — Create a Slack app

1. Go to https://api.slack.com/apps
2. Click **Create New App** → **From scratch**
3. App name: `In-Home-Care Bot`
4. Pick your workspace → **Create App**

### Step 2 — Add bot token scopes

Go to **OAuth & Permissions** → scroll to **Scopes** → under **Bot
Token Scopes**.

**Which scopes to add depends on your Slack plan:**

#### Free / Pro workspace (most users)

| Scope | Why |
|---|---|
| `channels:read` | List channels |
| `groups:read` | List private channels |
| `chat:write` | Post threaded replies (the LangGraph bot) |
| `channels:join` | Bot can join public channels |

> **Note:** Free/Pro plans do not allow `channels:manage` or
> `groups:write` (Slack shows "only available to Enterprise
> customers"). The bot cannot auto-create channels on free plans —
> you create them manually in Step 5 below.

#### Enterprise Grid workspace

| Scope | Why |
|---|---|
| `channels:manage` | Create and archive public channels |
| `channels:read` | List channels |
| `groups:write` | Create and archive private channels |
| `groups:read` | List private channels |
| `chat:write` | Post threaded replies (the LangGraph bot) |

> With Enterprise scopes, `npm run setup:slack:channels` auto-creates
> all 4 channels via the Slack API.

### Step 3 — Install to workspace

Click **Install to Workspace** → **Allow**. You'll get a **Bot User
OAuth Token** that starts with `xoxb-`.

### Step 4 — Export the token

```bash
export SLACK_BOT_TOKEN=xoxb-your-token-here
```

For GitHub Actions, add `SLACK_BOT_TOKEN` as a **repo secret**
(Settings → Secrets and variables → Actions → New repository secret).

The token is **never committed** to the repo. The `.gitignore` already
excludes `.env` files. If you prefer a `.env` file locally:

```bash
echo "SLACK_BOT_TOKEN=xoxb-your-token-here" >> .env
```

### Step 5 — Create the channels

#### Enterprise plan (auto-create)

```bash
npm run setup:slack:channels
```

Output:

```
Processing 4 channel(s):
  CREATED #in-home-help-field-officers (C07XXXXXXXX)
  CREATED #in-home-help-customer-support (C07XXXXXXXX)
  CREATED #in-home-help-product-owners (C07XXXXXXXX)
  CREATED #in-home-help-customers (C07XXXXXXXX)
Done. 4/4 channels ready.
```

#### Free / Pro plan (manual create — 30 seconds)

Create each channel manually in Slack:

1. Click **"+"** next to "Channels" in the sidebar
2. Create these 4 channels:
   - `in-home-help-field-officers`
   - `in-home-help-customer-support`
   - `in-home-help-product-owners`
   - `in-home-help-customers`
3. Invite the bot to each channel — type in each channel:
   ```
   /invite @In-Home-Care Bot
   ```

Then verify:

```bash
npm run status:slack:channels
```

### Check channel status

```bash
npm run status:slack:channels
```

Shows ACTIVE / ARCHIVED / NOT FOUND for each channel plus member count.
Works on **all Slack plans** (only needs `channels:read`).

### Tear down channels

**Enterprise plan:**

```bash
npm run teardown:slack:channels
```

Archives (soft-deletes) all four channels.

**Free / Pro plan:** archive channels manually from Slack (right-click
channel → "Archive channel").

### Adding or renaming channels

Edit `DevOps/Slack/channels.json` — add, remove, or rename entries —
then re-run `npm run setup:slack:channels`. The script reads from that
file every time.

## Status

Scaffolded. Directory structure, architecture diagram, and dev plan
committed. Block 1 (skeleton + smoke tests per service) is the next
iteration.
