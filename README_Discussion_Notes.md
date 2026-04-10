# Discussion Notes — In-Home-Care-Platform

Running log of every design decision, question, and direction change
since this repo was started. Newest entries at the bottom.

---

## 1. Origin — whiteboard sketch (2026-04-10)

The repo started from a whiteboard photo (`20260410_193206.jpg`) that
sketched the full platform architecture. The whiteboard showed:

**Three personas entering via Slack channels + dedicated apps:**
- Staff Field (Mobile App) → Slack Channel 1
- Customer Support (Desktop App) → Slack Channel 2
- Admin Staff (React Web App) → Slack Channel 3

**Central middleware layer:**
- React Portal Admin (web app)
- Mongo Central + FastAPI
- ADK Gateway (Google ADK)
- Events → Kafka
- MCP Tool (FastMCP)
- Microservices: Customer/Member Visit Mgmt, Visit Ingest, GCP Doc
  Intelligence, DS/Doc Intelligence

**Agentic layer:**
- LangGraph → VectorDB + Microservice Invoke + Tools + LLM
- Slack Channel Responder → Final Slack Response
- "Visit Intelligence" written prominently in the center

**Decision:** Build this as a single monorepo where each folder is
conceptually a separate service/app.

## 2. Repo naming discussion

**Constraint:** Cannot use "RiteCare" — the repo simulates
`https://theritecare.com/` but the name can't be used due to legal
concerns. Need a generic, professional name that describes the domain
(in-home healthcare delivery / field visit operations) without
referencing any real product.

**Options considered:**
- `home-care-ops-platform`
- `field-care-ops-platform`
- `care-visit-platform`
- `in-home-care-platform`
- `care-ops-platform`

**Decision:** `in-home-care-platform` — most descriptive of the
industry vertical without touching any brand name.

## 3. Features from theritecare.com (2026-04-10)

User referenced `https://theritecare.com/book-appointment/` and asked
to simulate:

1. **Book appointment** — service type, preferred date/time, service area
2. **Sign up / sign in** — member registration + authentication
3. **Visit listing** — upcoming and past visits for a patient/member
4. **Field officers** — mobile-first workflow for in-home staff

These became the core user stories the middleware services map to.

## 4. Monorepo structure decision

**Decision:** Single repo, multiple folders, each conceptually a
separate service:

```
middleware/Microservices/<service_name>/
middleware/AgenticFlows/<flow_name>/
portals/web_apps/<app_name>/
portals/mobile_app/<app_name>/
portals/desktop_app/<app_name>/
```

**Not separate git repos.** Shared infrastructure and documentation live
at the root. Each middleware folder has its own `requirements.txt` +
`src/` + `tests/`.

## 5. Microservices identified (from whiteboard)

Eight microservices under `middleware/Microservices/`:

| Service | Owns | Purpose |
|---|---|---|
| `api_gateway` | — (routes only) | FastAPI gateway, JWT auth, rate limiting |
| `auth_svc` | users, sessions | Sign up / sign in / token management |
| `member_svc` | members | Patient/member profile CRUD |
| `appointment_svc` | appointments | Book / cancel / reschedule |
| `visit_management_svc` | visits | Visit lifecycle + listing |
| `visit_ingest_svc` | visit_documents | Field data upload from mobile |
| `document_intelligence_svc` | extracted_fields | GCP Document AI OCR |
| `mcp_gateway` | — (tools only) | FastMCP + ADK gateway for LLM tools |

## 6. Agentic flows identified (from whiteboard)

Three LangGraph workflows under `middleware/AgenticFlows/`:

| Flow | Trigger | Purpose |
|---|---|---|
| `visit_intelligence_flow` | Visit completion event | Score visit, detect gaps, write dispositions |
| `slack_channel_responder_flow` | Slack message | Classify, retrieve, answer, reply in-thread |
| `document_author_flow` | Doc AI extraction done | Draft visit summaries for staff review |

## 7. Portals identified (from whiteboard)

Four client apps under `portals/`:

| App | Persona | Features |
|---|---|---|
| `member_portal` (React) | Members/patients | Book appointment, view visits, profile |
| `care_admin_portal` (React) | Admin staff | Dashboard, staff mgmt, visit review |
| `field_staff_app` (mobile) | Field officers | Today's assignments, visit recording, camera |
| `customer_support_app` (desktop) | Customer support | Member lookup, case creation, call handling |

## 8. Removed `infrastructure/` folder

**Question:** "do we need infrastructure folder since we have
DevOps/Local folder?"

**Decision:** No — redundant. All docker-compose stacks consolidated
under `DevOps/Local/`. Removed `infrastructure/` entirely and moved
MongoDB + Kafka compose files to `DevOps/Local/MongoDB/` and
`DevOps/Local/Kafka/`.

## 9. DevOps/Local stacks requested (2026-04-10)

User requested full local infrastructure under `DevOps/Local/`:

| Stack | Port | Purpose |
|---|---|---|
| MongoDB | 27017 | Central data store |
| Kafka | 9092 | Event streaming |
| Postgres | 5432 | Relational (auth, scheduling) |
| Redis | 6379 | Caching, rate limiting, sessions |
| Qdrant | 6333 | Vector DB (default) |
| Weaviate | 8080 | Vector DB (alt) |
| Chroma | 8000 | Vector DB (alt) |
| Milvus | 19530 | Vector DB (alt) |
| pgvector | 5433 | Vector DB (alt, Postgres-based) |
| Prometheus | 9090 | Metrics scraping |
| Grafana | 3000 | Dashboards |
| Kibana + Elasticsearch | 5601 / 9200 | Log search (ELK stack) |

Control scripts: `docker-all-up.sh`, `docker-all-down.sh`,
`docker-all-status.sh` — each iterates over every compose file.

## 10. Requirements files decision

**Per-folder:** Each `middleware/Microservices/<svc>/requirements.txt`
and `middleware/AgenticFlows/<flow>/requirements.txt` lists only the
dependencies that service needs. Production deploys install per-folder.

**Consolidated root:** `requirements.txt` at the repo root installs
everything — all services, all flows, all extras (pandas, numpy,
vector DBs, observability, testing). Used for local dev only so one
`pip install -r requirements.txt` gives you the full monorepo.

## 11. package.json npm task runner

**Decision:** Use `package.json` as the local dev task runner (not
Makefile, not just bash). All commands invokable via `npm run <task>`.

Tasks implemented:

| Script | Purpose |
|---|---|
| `setup:local:all` | Create conda venv + pip install + docker up |
| `setup:local:venv:create` | `conda create -y -p ~/runtime_data/python_venvs/In-Home-Care-Platform python=3.13` |
| `setup:local:venv:install` | `pip install -r requirements.txt` into the conda venv |
| `setup:local:venv:activate` | Prints the `conda activate` command |
| `setup:local:venv:deactivate` | Prints `conda deactivate` |
| `setup:local:venv:destroy` | `rm -rf` the venv dir |
| `setup:local:docker:up/down/status` | Docker-compose control scripts |
| `local:middleware:start-all` | Uvicorn all 8 services (ports 8001-8008) |
| `local:middleware:stop-all` | Kill all middleware PIDs |
| `local:middleware:status-all` | Check PID liveness |
| `local:portals:start-all` | Vite dev servers (ports 3001-3002) |
| `local:portals:stop-all` | Kill portal PIDs |
| `local:portals:status-all` | Check PID liveness |
| `local:start-all` | Docker + middleware + portals in one go |
| `local:stop-all` | Reverse of above |
| `teardown:local:all` | Stop everything + destroy conda venv |
| `test` | `pytest -q` via the conda venv Python |
| `lint` | `ruff check .` via the conda venv Python |

**Conda venv location:** `$HOME/runtime_data/python_venvs/In-Home-Care-Platform`
(follows the pattern from Member-Event-Stream-Agent).

## 12. AWS deployment workflows (2026-04-10)

User requested modular AWS deployment via GitHub Actions workflows:

| Workflow | Purpose |
|---|---|
| `AWS_001_Setup_Create_VPC` | VPC + 2 public + 2 private subnets + IGW |
| `AWS_002_Setup_Create_S3_EFS` | S3 bucket (versioned, encrypted) + EFS |
| `AWS_003_Setup_Create_ECR_ECS` | ECR repos (one per microservice) + ECS Fargate cluster |
| `AWS_004_Setup_Create_APIGW` | HTTP API Gateway |
| `AWS_005_Setup_DBs` | DocumentDB + ElastiCache Redis + MSK reference |
| `AWS_006_Setup_Bedrock` | Verify model access + knowledge base reference |
| `AWS_097_Create_All` | Orchestrator: chains 001→006 sequentially |
| `AWS_097_Check_Create_Status` | Queries every resource, prints status tables |
| `AWS_100_Destroy_All` | Tears down everything (requires `confirm=DESTROY`) |

All resources tagged `Project=in-home-care-platform`, `Env=<env_name>`.
Auth via `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY` repo secrets.

**Design decision:** Same numbered-prefix pattern as the GCP workflows
in Member-Event-Stream-Agent (`GCP_001` → `GCP_100`), but for AWS.

## 13. Portal tech stack decision (2026-04-10)

**Question:** "using which stack you think we should create DesktopApp
and also MobileApp that runs locally in this laptop"

**Decision:**

| Portal | Stack | Why |
|---|---|---|
| Web apps (member_portal + care_admin_portal) | React + Vite + Tailwind CSS | Fast dev, full color control |
| Desktop app (customer_support_app) | Electron + React | Same codebase shape as web; runs natively on Mac |
| Mobile app (field_staff_app) | React Native (Expo) | Same JS/TS; runs on laptop via Expo Go; camera support |

## 14. Color palette + design rules (2026-04-10)

**User preference:** "no gray no light please I hate those colors and
also good logo"

**Decision — bold healthcare-warm palette:**

| Role | Color | Hex |
|---|---|---|
| Primary | Deep teal | `#0D7377` |
| Secondary / CTA | Warm orange | `#E8612D` |
| Background | Clean white | `#FFFFFF` |
| Text | Dark navy | `#1A2B3C` |
| Success | Forest green | `#2D8A4E` |
| Danger / error | Crimson | `#D32F2F` |
| Info / links | Bright blue | `#1976D2` |

**Rules:**
- No gray backgrounds (ever).
- No light/washed-out text.
- Buttons must have strong contrast (teal or orange on white).
- Logo: simple SVG mark (house + heart or house + care cross) in the
  teal/orange palette.
- Favicon: 32x32 + 16x16 PNG from the SVG logo.

## 15. Architecture diagram — 7 tabs (2026-04-10)

`Docs/Design/architecture.drawio` committed with 7 tabs derived from
the whiteboard:

1. System Overview (full whiteboard redrawn)
2. Book Appointment Flow (member → API GW → appointment_svc → Kafka → visit_management_svc → push to field staff)
3. Auth — Sign Up + Sign In (JWT + 4 roles)
4. Visit Listing + Lifecycle (SCHEDULED → IN_PROGRESS → COMPLETED → REVIEWED + CANCELLED branch)
5. Microservice Map (8 services, what they own, who they talk to)
6. LangGraph Agentic Flows (3 workflows: slack responder, visit intelligence, document author)
7. Data Model (MongoDB collections grouped by owning service + VectorDB namespaces)

## 16. Next: scaffold portals with the color system + logo + favicons

Pending — this is the next block of work after this discussion notes
file is committed.

---

*This file is append-only. New entries go at the bottom with the next
number.*
