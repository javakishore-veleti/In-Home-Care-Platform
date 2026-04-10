# Development Plan — In-Home-Care-Platform

Monorepo punch list. Each block builds one layer or feature. Blocks
are ordered for maximum early demo value (auth + member + appointment
first so the book-appointment flow works end to end).

Legend: `[ ]` not started · `[~]` in progress · `[x]` done

## Block 0 — Scaffold + local infra

- [ ] **T0.1** Directory structure, per-folder READMEs, per-folder
       `requirements.txt`, consolidated root `requirements.txt`.
- [ ] **T0.2** `package.json` npm task runner — `setup:local:all`,
       `setup:local:venv:create/install/activate/deactivate/destroy`,
       `setup:local:docker:up/down/status`.
- [ ] **T0.3** `DevOps/Local/` docker-compose stacks — MongoDB,
       Kafka, Postgres, Redis, 5 VectorDBs, Prometheus, Grafana,
       Kibana (ELK). Control scripts `docker-all-up/down/status.sh`.
- [ ] **T0.4** `Docs/Design/architecture.drawio` — 7 tabs mapping
       the whiteboard.
- [ ] **T0.5** `npm run setup:local:all` creates the conda venv,
       installs requirements, and brings up all docker stacks.

## Block 1 — auth_svc

- [ ] **T1.1** Pydantic models: `User`, `SignUpRequest`, `SignInRequest`.
- [ ] **T1.2** `MongoStore` for users + sessions.
- [ ] **T1.3** Routes: `POST /auth/signup`, `POST /auth/signin`.
- [ ] **T1.4** JWT issue + verify. Roles: `member`, `field_staff`,
       `support`, `admin`.
- [ ] **T1.5** Tests against mongomock.

## Block 2 — member_svc

- [ ] **T2.1** Pydantic models: `Member` (PII-tagged fields).
- [ ] **T2.2** `MongoStore` for members. Tenant-scoped.
- [ ] **T2.3** Routes: `POST /members`, `GET /members/{id}`,
       `PATCH /members/{id}`.
- [ ] **T2.4** Tests.

## Block 3 — appointment_svc (Book Appointment)

- [ ] **T3.1** Pydantic models: `Appointment`, `BookRequest`.
- [ ] **T3.2** `MongoStore` for appointments.
- [ ] **T3.3** Routes: `POST /appointments`, `GET /appointments/{id}`,
       `PATCH /appointments/{id}/cancel`.
- [ ] **T3.4** Kafka producer: publish `appointment.booked` event.
- [ ] **T3.5** Tests (mongomock + InMemoryBus for Kafka).

## Block 4 — visit_management_svc (Visit Listing + Lifecycle)

- [ ] **T4.1** Pydantic models: `Visit`, `VisitStatus` enum.
- [ ] **T4.2** `MongoStore` for visits. Status transitions enforced.
- [ ] **T4.3** Kafka consumer: create pending visit on
       `appointment.booked`.
- [ ] **T4.4** Routes: `GET /visits?member_id=...`,
       `GET /visits?staff_id=...`, `PATCH /visits/{id}/status`.
- [ ] **T4.5** Tests.

## Block 5 — api_gateway

- [ ] **T5.1** FastAPI app factory. JWT middleware reads token from
       `auth_svc`, enforces role ACL per route.
- [ ] **T5.2** Reverse-proxy routing to all downstream services.
- [ ] **T5.3** `/healthz`, `/version`.
- [ ] **T5.4** Tests: auth happy path, 401, 403 per role.

## Block 6 — visit_ingest_svc + document_intelligence_svc

- [ ] **T6.1** `visit_ingest_svc`: `POST /visits/{id}/documents`
       file upload, stores raw doc in MongoDB.
- [ ] **T6.2** `document_intelligence_svc`: GCP Document AI wrapper
       with `FakeDocAIClient` for tests. Stores extracted_fields.
- [ ] **T6.3** Tests with MagicMock for Doc AI.

## Block 7 — mcp_gateway

- [ ] **T7.1** FastMCP server registering tools: `member_lookup`,
       `visit_history`, `appointment_status`, `document_search`.
- [ ] **T7.2** Token auth + per-tool scope enforcement + audit log.
- [ ] **T7.3** Tests via fastmcp in-process Client.

## Block 8 — AgenticFlows (LangGraph)

- [ ] **T8.1** `slack_channel_responder_flow`: Classifier → Retriever
       → Answerer → Responder. slack-bolt integration. Tests with
       FakeLlmClient + FakeVectorClient + FakeSlackClient.
- [ ] **T8.2** `visit_intelligence_flow`: triggered on visit
       completion Kafka event. Scorer → Gap Detector → Disposition.
- [ ] **T8.3** `document_author_flow`: triggered after Doc AI
       extraction. Summarizer → Draft Writer.

## Block 9 — Portals (frontend scaffold)

- [ ] **T9.1** `member_portal`: React + Vite + Tailwind. Pages:
       sign up, sign in, book appointment, visit list, profile.
- [ ] **T9.2** `care_admin_portal`: React + Vite + Tailwind.
       Dashboard, staff management, visit review.
- [ ] **T9.3** `field_staff_app`: React Native or Flutter scaffold.
       Today's assignments, visit recording, camera upload.
- [ ] **T9.4** `customer_support_app`: Electron / Tauri scaffold.
       Member lookup, case creation, appointment booking on behalf.

## Block 10 — Observability + CI

- [ ] **T10.1** structlog with PII-aware processor across all
       middleware services.
- [ ] **T10.2** Prometheus metrics endpoint on api_gateway + mcp_gateway.
- [ ] **T10.3** Grafana dashboard JSON provisioning.
- [ ] **T10.4** `.github/workflows/ci.yml` — pytest per-service on
       every push and PR to `main`.
- [ ] **T10.5** `npm test` green locally and in CI.

## Definition of done

1. `npm run setup:local:all` creates the conda venv, installs
   requirements, and brings up all docker stacks without errors.
2. `npm test` green (pytest across all middleware services).
3. Book appointment end-to-end: member_portal → api_gateway →
   appointment_svc → Kafka → visit_management_svc → visit shows in
   member portal.
4. Slack channel responder answers a question with cited sources in
   a thread reply.
5. Every block lands as its own commit.

## Status

Scaffold committed. Block 0 is landing now.
