# In-Home-Care-Platform

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

## Status

Scaffolded. Directory structure, architecture diagram, and dev plan
committed. Block 1 (skeleton + smoke tests per service) is the next
iteration.
