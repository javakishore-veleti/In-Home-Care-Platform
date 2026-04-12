# Knowledge Base — Brainstorming Document

> **Status**: Phase 1 complete, Phase 2 (pgvector) live, Phase 2c–4 next.
> Read, annotate, push back on anything, then tell Claude "build phase N" when ready.
>
> **Last updated**: 2026-04-12

---

## Table of Contents

- [1. The Insight](#1-the-insight)
- [2. Glean Parallel](#2-glean-parallel)
- [3. How It Maps to What We Already Have](#3-how-it-maps-to-what-we-already-have)
- [4. End-to-End User Story](#4-end-to-end-user-story)
- [5. Architecture Diagram](#5-architecture-diagram)
- [6. Existing Components That Plug In Directly](#6-existing-components-that-plug-in-directly)
- [7. Build Phases](#7-build-phases)
  - [Phase 1a — Collections CRUD](#phase-1a--collections-crud)
  - [Phase 1b — Repositories + Items + File Upload](#phase-1b--repositories--items--file-upload)
  - [Phase 2a — pgvector Indexing (inline pipeline)](#phase-2a--pgvector-indexing-inline-pipeline)
  - [Phase 2b — Multi-Strategy Chunking](#phase-2b--multi-strategy-chunking)
  - [Phase 2c — RAG Search API](#phase-2c--rag-search-api)
  - [Phase 3 — LangGraph Briefing Agent + Slack Auto-Response](#phase-3--langgraph-briefing-agent--slack-auto-response-3-days)
  - [Phase 4 — Interactive Slack Q&A](#phase-4--interactive-slack-qa-2-days)
  - [Phase 5 — Airflow + S3 + Multi-Tenant](#phase-5--airflow--s3--multi-tenant)
- [8. Key Technical Decisions](#8-key-technical-decisions)
- [9. Data Model (Draft)](#9-data-model-draft)
- [10. LangGraph Flow Design](#10-langgraph-flow-design)
- [11. Slack Threading UX](#11-slack-threading-ux)
- [12. What Makes This a Moat](#12-what-makes-this-a-moat)
- [13. Open Questions](#13-open-questions)
- [14. Research Insights — Papers to Incorporate](#14-research-insights--papers-to-incorporate)
  - [14.1 EICopilot — Query Masking for Intent-Based RAG](#141-eicopilot-baidu-arxiv-250113746--query-masking-for-intent-based-rag)
  - [14.2 LiveVectorLake — Temporal Vector Lake](#142-livevectorlake-arxiv-260105270--temporal-vector-lake-for-mutable-enterprise-knowledge)
  - [14.3 Combined Impact on Data Model](#143-combined-impact-on-our-phase-2-data-model)
- [15. Multi-Jurisdiction Knowledge Scoping](#15-multi-jurisdiction-knowledge-scoping)
  - [15.1 The Problem](#151-the-problem)
  - [15.2 Industry Patterns](#152-how-industry-saas-companies-solve-this)
  - [15.3 Real-World Validation](#153-real-world-validation)
  - [15.4 Proposed Data Model Changes](#154-proposed-data-model-changes)
  - [15.5 RAG Query Changes](#155-how-the-rag-query-changes)
  - [15.6 Pricing & Packaging](#156-pricing-and-packaging-implications)
  - [15.7 Implementation Phasing](#157-implementation-phasing)
- [16. Admin Portal — Knowledge Base Menu & Repository Model](#16-admin-portal--knowledge-base-menu--repository-model)
  - [16.1 Navigation Hierarchy](#161-navigation-hierarchy)
  - [16.2 Page-by-Page UX](#162-page-by-page-ux)
  - [16.3 Repository Item Types](#163-repository-item-types)
  - [16.4 Repository Lifecycle](#164-repository-lifecycle)
  - [16.5 Source Locations — Folder / S3](#165-source-locations--folder--s3)
  - [16.6 Kafka → Airflow Async Indexing Pipeline](#166-kafka--airflow-async-indexing-pipeline)
  - [16.7 Why Airflow](#167-why-airflow-not-inline-in-knowledge_svc)
  - [16.8 Updated Data Model](#168-updated-data-model-replaces-section-9)
  - [16.9 Airflow DAG Sketch](#169-airflow-dag-sketch-python)
  - [16.10 Updated Phase Plan](#1610-updated-phase-plan-incorporating-repositories--airflow)
- [17. Multi-Strategy Chunking for RAG](#17-multi-strategy-chunking-for-rag)
  - [17.1 Why One Strategy Is Not Enough](#171-why-one-strategy-is-not-enough)
  - [17.2 The Four Strategies](#172-the-four-strategies)
  - [17.3 Storage Design — Same Table, Strategy Column](#173-storage-design--same-table-strategy-column)
  - [17.4 How Retrieval Uses Multiple Strategies](#174-how-retrieval-uses-multiple-strategies)
  - [17.5 De-Duplication of Overlapping Chunks](#175-de-duplication-of-overlapping-chunks)
  - [17.6 How the LLM Sees It](#176-how-the-llm-sees-it)
  - [17.7 Storage Math](#177-storage-math)
  - [17.8 Implementation Plan](#178-implementation-plan)
- [18. Implementation Status](#18-implementation-status)
- [19. Multi-LLM Fan-Out, Token Economics & Observability](#19-multi-llm-fan-out-token-economics--observability)
  - [19.1 The Concept](#191-the-concept)
  - [19.2 Architecture](#192-architecture)
  - [19.3 Model Registry](#193-model-registry)
  - [19.4 Data Model — llm_responses](#194-data-model--llm_responses)
  - [19.5 Token Economics Tracking](#195-token-economics-tracking)
  - [19.6 Prometheus Metrics](#196-prometheus-metrics)
  - [19.7 Grafana Dashboards](#197-grafana-dashboards)
  - [19.8 Kibana Logging](#198-kibana-elk-logging)
  - [19.9 Appointment Detail — LLM Responses Listing](#199-appointment-detail--llm-responses-listing)
  - [19.10 Updated Phase Plan](#1910-updated-phase-plan)
  - [19.11 Airflow Fan-Out + Per-User Model Override](#1911-airflow-fan-out--per-user-model-override)

---

## 1. The Insight

Glean's core value proposition is:

> *Organize knowledge by business context (collections), index it for
> semantic search, and surface it in the workflow where the employee is
> already working.*

We apply the same pattern **vertically to in-home healthcare**:

- **Collections** = appointment service types (the Create Appointment
  dropdown: "Personal Care & Companionship", "Skilled Nursing",
  "Physical Therapy", "Home Health Aide", etc.)
- **Collection items** = Documents (care protocols, compliance PDFs),
  Announcements (policy updates), Links (training videos, external
  clinical guidelines), Notes (clinical tips, common field-staff
  questions)
- **The workflow** = Slack. The moment a field officer claims an
  appointment, the system automatically posts a contextual briefing
  **in the same Slack thread**: "Here's what you need to know for this
  Personal Care & Companionship visit — top 3 relevant care protocols,
  the latest announcement about updated hygiene guidelines, and a link
  to the training video for this service type."

The billion-dollar part: **knowledge meets the person at the moment
they need it, in the tool they're already in.** Glean charges
\$10–25/user/month for this in horizontal enterprise; we'd own it for
in-home healthcare with domain-specific depth no horizontal tool can
match.

---

## 2. Glean Parallel

| Glean concept | Our equivalent | Notes |
|---|---|---|
| Collection | Service-type knowledge group | Auto-seeded from `appointment.service_type` dropdown values. Admin can also create custom ones. |
| Documents | Care protocols, compliance PDFs, SOPs | Uploaded by admin, OCR'd by `document_intelligence_svc` (GCP Document AI), chunked, embedded, stored in VectorDB. |
| Announcements | Policy updates, seasonal guidelines | Rich-text entries created by admin, timestamped so the most recent one surfaces first. |
| Links | Training videos, external clinical resources | URL + scraped/summarized content indexed alongside documents. |
| Notes | Clinical tips, Q&A from experienced staff | Short-form text, directly embedded. Think internal wiki snippets. |
| Custom agentic workflows | LangGraph `knowledge_briefing_flow` | Triggered automatically on appointment.claimed, or interactively when a field officer asks a question in a Slack thread. |
| Glean search bar | RAG query API + Slack Q&A thread | `POST /knowledge/search` for programmatic access, Slack threaded reply for conversational access. |

---

## 3. How It Maps to What We Already Have

```
                  ┌──────────────────────────────────────────────────┐
                  │                EXISTING (built today)             │
                  │                                                  │
  Member books ──►│ appointment_svc ──► Kafka appointment.booked     │
                  │                          │                       │
                  │                     slack_svc consumer            │
                  │                          │                       │
                  │                     Slack #channel (Claim btn)    │
                  │                          │                       │
                  │                     Claim clicked                 │
                  │                          │                       │
                  │                     appointment_svc /claim        │
                  │                     status='claimed'              │
                  └──────────────────────────────────────────────────┘
                                             │
                                             ▼  NEW
                  ┌──────────────────────────────────────────────────┐
                  │          appointment.claimed event → Kafka        │
                  │                          │                       │
                  │                     knowledge_agent_svc          │
                  │                     (LangGraph agent)            │
                  │                          │                       │
                  │          ┌───────────────┼───────────────┐       │
                  │          ▼               ▼               ▼       │
                  │    appointment_svc  VectorDB (RAG)   LLM API    │
                  │    (member profile, (collection docs, (synthesize │
                  │     visit history)   protocols, notes)  briefing) │
                  │          │               │               │       │
                  │          └───────────────┼───────────────┘       │
                  │                          ▼                       │
                  │                  Slack threaded reply             │
                  │           "Here's your briefing for this         │
                  │            Personal Care visit..."               │
                  └──────────────────────────────────────────────────┘
```

---

## 4. End-to-End User Story

### Story A — Automatic briefing on Claim

1. **Admin** opens `http://127.0.0.1:3002/app/knowledge-base`, navigates
   to the "Personal Care & Companionship" collection, and uploads three
   PDFs: a care protocol, a hygiene-guidelines update, and a medication
   reminder checklist.
2. The system OCR's each PDF (via `document_intelligence_svc`), chunks
   the text (~512 tokens/chunk), embeds each chunk (OpenAI
   `text-embedding-3-small`), and stores them in the VectorDB with
   `collection_id` metadata.
3. A **member** books a "Personal Care & Companionship" appointment via
   the member portal.
4. The appointment lands in Slack
   `#in-home-help-member-appointment-requests` with a **Claim** button
   (existing flow).
5. **Field officer** clicks **Claim**. The Slack message updates to
   "Claimed by @field_officer" (existing flow).
6. Within 2 seconds, a **threaded reply** appears under the same
   message:

   > **Care briefing for Personal Care & Companionship**
   >
   > Based on 3 knowledge-base documents:
   >
   > 1. **Hygiene guidelines (updated 2026-04-10)** — Always wear
   >    gloves during personal care tasks. Sanitize hands before and
   >    after each visit. [Full doc →]
   > 2. **Medication reminder checklist** — Confirm the member's
   >    medication schedule before starting care. Document any missed
   >    doses. [Full doc →]
   > 3. **Care protocol v4.2** — Follow the 5-step arrival procedure:
   >    identify yourself, confirm member identity, review today's
   >    care plan, check emergency contacts, begin service.
   >
   > *Member M-42 has 2 prior visits — last visit noted "prefers
   > morning routines before 9 AM".*

7. The field officer reads the briefing in Slack, asks a follow-up
   question in the thread: "What are the mobility restrictions for
   this member?" — the agent responds with a grounded answer from the
   knowledge base + member history.

### Story B — Admin knowledge management

1. Admin signs into the admin portal → **Knowledge Base** in the
   sidebar.
2. Sees a card grid of collections — one per service type, auto-seeded
   from the appointment dropdown values. Each card shows: name, item
   count, last updated.
3. Clicks "Skilled Nursing" → item list: 5 documents, 2
   announcements, 1 link, 3 notes.
4. Clicks **+ Add item** → picks type (Document / Announcement / Link
   / Note) → fills the form → saves.
5. For Documents: drag-and-drop file upload → progress bar → "Indexed
   12 chunks" confirmation.
6. The new knowledge is available to the next LangGraph briefing
   within seconds — no re-deploy, no re-index-all.

---

## 5. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           ADMIN PORTAL                                  │
│  Knowledge Base page: collections grid → item list → upload / create    │
│  Each collection maps to an appointment service_type                    │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ REST API
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         API GATEWAY (:8001)                              │
│  /api/admin/knowledge/collections                                       │
│  /api/admin/knowledge/collections/{id}/items                            │
│  /api/admin/knowledge/collections/{id}/items/{id}/upload                │
│  /api/admin/knowledge/search                                            │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    ▼                ▼                ▼
          ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐
          │knowledge_svc│  │document_intel│  │ VectorDB         │
          │  :8010      │  │  _svc :8007  │  │ (pgvector in     │
          │             │  │              │  │  Postgres, or    │
          │ Collections │  │ PDF → OCR →  │  │  Qdrant :6333)   │
          │ Items CRUD  │  │ extracted    │  │                  │
          │ Chunking    │  │ text         │  │ collection_chunks│
          │ Embedding   │  │              │  │ (vector, text,   │
          │ Search API  │  │              │  │  item_id,        │
          └──────┬──────┘  └──────────────┘  │  collection_id)  │
                 │                           └────────┬─────────┘
                 │ Kafka: item.indexed                │
                 │ (future: incremental re-index)     │
                 │                                    │
                 ▼                                    │
┌─────────────────────────────────────────────────────┤
│              KAFKA                                   │
│  appointment.booked  ← (existing)                    │
│  appointment.claimed ← (NEW: produced on Claim)      │
│  item.indexed        ← (NEW: produced on item save)  │
└────────────────────────────────────┬─────────────────┘
                                     │ consume appointment.claimed
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    knowledge_agent_svc (:8011)                           │
│                    (LangGraph agentic flow)                              │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  knowledge_briefing_flow (LangGraph StateGraph)                 │    │
│  │                                                                 │    │
│  │  START                                                          │    │
│  │    ↓                                                            │    │
│  │  fetch_appointment  ← HTTP → appointment_svc                    │    │
│  │    ↓                   (service_type, member_id, ...)           │    │
│  │  fetch_member_history ← HTTP → member_svc / visit_mgmt_svc     │    │
│  │    ↓                   (last N visits, notes)                   │    │
│  │  rag_retrieve  ← HTTP → knowledge_svc /search                  │    │
│  │    ↓            (query=service_type context, collection=slug)   │    │
│  │  synthesize_briefing  ← LLM API (Claude / GPT-4o / ADK)        │    │
│  │    ↓                   (system prompt + RAG chunks + history)   │    │
│  │  post_to_slack  ← shared/slack.py post_message(thread_ts=...)   │    │
│  │    ↓                                                            │    │
│  │  END                                                            │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  Future: interactive Q&A handler (Slack Events API message.channels)    │
│  User replies in thread → same RAG pipeline → threaded LLM response    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Existing Components That Plug In Directly

| Component | Current status | Role in knowledge base |
|---|---|---|
| Kafka `appointment.events` topic | ✅ running, slack_svc consumes it | Add `appointment.claimed` event type; knowledge_agent_svc subscribes |
| VectorDB Docker composes | ✅ in repo (Qdrant, Weaviate, Chroma, Milvus, pgvector) — currently commented out | Uncomment pgvector (or Qdrant) in `docker-all-up.sh`; add `wait-for-vectordb.sh` |
| `document_intelligence_svc` (:8007) | ✅ exists, has GCP Document AI OCR | Upload PDF → call doc_intel for OCR → receive extracted text → feed into chunking |
| `mcp_gateway` (FastMCP + ADK) | ✅ exists | Expose knowledge search as MCP tools the LangGraph agent calls |
| LangGraph flows | ✅ architecture-designed (`visit_intelligence_flow`, `slack_channel_responder_flow`, `document_author_flow`) | `knowledge_briefing_flow` follows the exact same pattern |
| `shared/slack.py` post_message | ✅ working, posts Block Kit | Add `thread_ts` parameter for threaded replies |
| `slack_channel_integrations` table | ✅ built today | Add `appointment.claimed` event_type mapping so the briefing response goes to the configured channel |
| Admin portal | ✅ 7 pages, auth, RBAC | Add "Knowledge Base" nav entry + collection/item management pages |
| `.env.local` + middleware sourcing | ✅ built today | Add `OPENAI_API_KEY` (or `ANTHROPIC_API_KEY`) for embedding + LLM |
| `appointment_svc` claim flow | ✅ working, produces Kafka events | Produce `appointment.claimed` alongside the existing status bump |

---

## 7. Build Phases

Each phase is independently shippable and testable. You can stop after
any phase and have a working feature — each subsequent phase extends it.

### Phase 1 — Collections + Items CRUD (~2 days)

**What ships**: admin portal page to manage knowledge collections and
items. No AI, no VectorDB — just the data model and CRUD.

**New microservice**: `knowledge_svc` (:8010)

**DB tables** (in `knowledge_schema`, managed by `knowledge_svc` alembic):

- `collections` (id, name, slug, service_type, description, icon_emoji,
  created_at, updated_at)
- `collection_items` (id, collection_id FK, item_type enum
  [document, announcement, link, note], title, content_text,
  source_url, file_path, file_size_bytes, mime_type,
  created_by_user_id, created_at, updated_at)

**Auto-seeding**: on startup, `knowledge_svc` reads distinct
`service_type` values from `appointment_schema.appointments` (or a
hard-coded seed list) and ensures one collection exists per type.

**Admin portal**:

- New nav entry: "Knowledge Base"
- Collection grid page: card per collection showing name, item count,
  last updated
- Collection detail page: item list with type badge, title, created
  date, actions (edit, delete)
- "Add item" form: type selector → fields vary by type (Document:
  file upload; Announcement: rich text; Link: URL; Note: plain text)
- File upload: `multipart/form-data` to
  `/api/admin/knowledge/collections/{id}/items/upload`

**API routes** (admin-gated):

```
GET    /api/admin/knowledge/collections
GET    /api/admin/knowledge/collections/{id}
POST   /api/admin/knowledge/collections
PATCH  /api/admin/knowledge/collections/{id}
DELETE /api/admin/knowledge/collections/{id}
GET    /api/admin/knowledge/collections/{id}/items
POST   /api/admin/knowledge/collections/{id}/items
POST   /api/admin/knowledge/collections/{id}/items/upload  (multipart)
PATCH  /api/admin/knowledge/items/{id}
DELETE /api/admin/knowledge/items/{id}
```

### Phase 2 — VectorDB Indexing + RAG Search (~2 days)

**What ships**: every item saved in Phase 1 gets chunked, embedded,
and stored in the VectorDB. A search API returns semantically relevant
chunks for any query scoped to a collection.

**VectorDB choice** (recommended: start with **pgvector**, graduate
to **Qdrant** when you need filtering + hybrid search):

| Option | Pros | Cons |
|---|---|---|
| pgvector (Postgres extension) | Zero new infra — same Postgres you already run. One `CREATE EXTENSION vector;` away. | No dedicated vector UI, limited filtering, cosine-sim-only. |
| Qdrant (:6333) | Best DX, built-in filtering, hybrid search, dashboard UI. | Another container to run + monitor. |
| Chroma | Lightest, great for prototyping. | Not production-grade for large datasets. |

**DB table** (or VectorDB collection):

```
knowledge_schema.collection_chunks (
  id           SERIAL PRIMARY KEY,
  item_id      INT NOT NULL REFERENCES collection_items(id) ON DELETE CASCADE,
  collection_id INT NOT NULL REFERENCES collections(id),
  chunk_index  INT NOT NULL,
  chunk_text   TEXT NOT NULL,
  embedding    VECTOR(1536),      -- pgvector; 1536 = OpenAI small dimension
  created_at   TIMESTAMPTZ DEFAULT now()
)
```

**Indexing pipeline** (runs inside `knowledge_svc` on item save):

```
Item saved (text or extracted-OCR text)
    ↓
Recursive character text splitter
    chunk_size=512 tokens, overlap=50 tokens
    ↓
For each chunk:
    embed via OpenAI text-embedding-3-small
    (or local sentence-transformers for zero-cost dev)
    ↓
INSERT into collection_chunks
    (item_id, collection_id, chunk_index, chunk_text, embedding)
```

**For Document uploads**: call `document_intelligence_svc` OCR first
to extract text from PDF/image, then feed extracted text into the
chunking pipeline above.

**Search API** (unauthenticated internal route for the LangGraph
agent, plus admin-gated version for the portal):

```
POST /api/admin/knowledge/search
POST /api/internal/knowledge/search

Body: {
  "collection_slug": "personal-care-companionship",
  "query": "What should I know before a personal care visit?",
  "top_k": 5
}

Response: {
  "results": [
    {
      "chunk_text": "Always wear gloves during personal care...",
      "item_title": "Hygiene Guidelines v4",
      "item_type": "document",
      "score": 0.89,
      "collection_name": "Personal Care & Companionship"
    },
    ...
  ]
}
```

**Env vars** added to `.env.local`:

```
OPENAI_API_KEY=sk-...
# or for local dev without API cost:
EMBEDDING_PROVIDER=sentence-transformers
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

### Phase 3 — LangGraph Briefing Agent + Slack Auto-Response (~3 days)

**What ships**: when a field officer claims an appointment, a threaded
Slack reply automatically appears within 2–5 seconds containing a
synthesized briefing from the knowledge base, personalized with the
member's visit history.

**New Kafka event**: `appointment.claimed`

- Produced by `appointment_svc.claim_appointment_via_slack()` right
  after the claim INSERT + status UPDATE (same transaction block we
  built today).
- Event payload: `{event_type: "appointment.claimed", appointment_id,
  slack_channel_id, slack_message_ts, claimed_by_slack_user_id,
  occurred_at}`.
- The `slack_channel_id` + `slack_message_ts` are critical — the
  LangGraph agent needs them to post a **threaded reply** under the
  correct Slack message.

**New microservice**: `knowledge_agent_svc` (:8011)

- FastAPI + lifespan Kafka consumer (same pattern as `slack_svc`)
- Subscribes to `appointment.events`, filters for
  `event_type == "appointment.claimed"`
- Runs the LangGraph flow

**LangGraph flow**: `knowledge_briefing_flow`

```python
from langgraph.graph import StateGraph, END

class BriefingState(TypedDict):
    appointment_id: int
    appointment: dict
    member_history: list[dict]
    rag_results: list[dict]
    briefing_text: str
    slack_channel_id: str
    slack_message_ts: str

graph = StateGraph(BriefingState)

graph.add_node("fetch_appointment", fetch_appointment)
graph.add_node("fetch_member_history", fetch_member_history)
graph.add_node("rag_retrieve", rag_retrieve)
graph.add_node("synthesize_briefing", synthesize_briefing)
graph.add_node("post_to_slack", post_to_slack)

graph.add_edge("fetch_appointment", "fetch_member_history")
graph.add_edge("fetch_member_history", "rag_retrieve")
graph.add_edge("rag_retrieve", "synthesize_briefing")
graph.add_edge("synthesize_briefing", "post_to_slack")
graph.add_edge("post_to_slack", END)

graph.set_entry_point("fetch_appointment")
briefing_flow = graph.compile()
```

**Node implementations** (sketch):

| Node | What it does | Calls |
|---|---|---|
| `fetch_appointment` | GET appointment by id, extract service_type, member_id | appointment_svc HTTP |
| `fetch_member_history` | GET last 3 visits + notes for the member | visit_management_svc HTTP (or MCP tool via mcp_gateway) |
| `rag_retrieve` | Search knowledge base for the appointment's service_type collection | knowledge_svc `/api/internal/knowledge/search` |
| `synthesize_briefing` | Pass RAG chunks + member history to LLM with a system prompt, get a 3-paragraph briefing | Claude API / OpenAI / ADK |
| `post_to_slack` | Post the briefing as a threaded reply under the claimed message | `shared/slack.py` `post_message(channel, text, blocks, thread_ts=...)` |

**LLM prompt** (draft):

```
You are a care coordinator for an in-home healthcare service.
A field officer just claimed an appointment for a {service_type} visit
with member M-{member_id} on {requested_date}.

Based on the following knowledge-base excerpts and member visit history,
write a concise briefing (3 short paragraphs) that the field officer
should read before the visit. Prioritize actionable information:
safety protocols, member preferences, and anything time-sensitive.

--- Knowledge Base ({collection_name}) ---
{rag_chunks_formatted}

--- Member Visit History ---
{visit_history_formatted}

--- Instructions ---
- Lead with the most important safety or compliance item.
- Mention any member-specific preferences from visit history.
- End with a reminder of any recent announcements or policy changes.
- Be concise — the field officer reads this on their phone in Slack.
- Cite the source document title for each fact.
```

**Slack threading**:

`shared/slack.py` `post_message` currently doesn't support threading.
Add an optional `thread_ts` parameter:

```python
def post_message(channel, text, blocks=None, thread_ts=None):
    payload = {'channel': channel, 'text': text}
    if blocks:
        payload['blocks'] = blocks
    if thread_ts:
        payload['thread_ts'] = thread_ts
    return _call('chat.postMessage', payload)
```

When the knowledge agent posts the briefing, it passes
`thread_ts=slack_message_ts` from the claimed appointment's Slack
message. The briefing appears as a threaded reply — the field officer
sees the original appointment card + the AI briefing in one thread.

### Phase 4 — Interactive Slack Q&A (~2 days)

**What ships**: field officers can reply in the Slack thread with a
question ("What are the mobility restrictions for this member?") and
get a grounded answer from the knowledge base + member history.

**Slack Events API subscription**: subscribe to `message.channels`
event type for the bot. When a user posts in a thread where the bot
has already replied, Slack sends the event to `/slack/events`.

**Handler flow**:

```
Slack Events API → /slack/events → slack_svc receives message event
    ↓
Extract: channel_id, thread_ts, user message text
    ↓
Determine context: which appointment is this thread about?
    (look up by thread_ts in appointment_slack_posts table)
    ↓
Re-run knowledge_briefing_flow with the user's question as the query
    (same RAG pipeline, but query = user question, not generic briefing)
    ↓
Post the LLM answer as another threaded reply
```

**This makes the Slack thread a conversational interface** to the
knowledge base. The field officer doesn't need to learn a new tool or
open a separate app — they just reply in the thread they're already
looking at.

---

## 8. Key Technical Decisions

Decisions I need your input on before building. Pick one per row and
I'll lock it in:

| Decision | Option A (recommended) | Option B | Option C |
|---|---|---|---|
| **VectorDB** | **pgvector** — zero new infra, same Postgres, fast to start. Graduate to Qdrant later. | Qdrant — better search quality, filtering, dedicated UI. Another container. | Chroma — lightest, good for prototyping, not production-grade. |
| **Embedding model** | **OpenAI `text-embedding-3-small`** — $0.02/1M tokens, 1536 dim, best quality/cost for production. | Local `sentence-transformers` (`all-MiniLM-L6-v2`) — free, 384 dim, slower, offline-capable. | Cohere `embed-english-v3.0` — good quality, $0.10/1M tokens. |
| **LLM for briefing** | **Claude API** (you're in the Anthropic ecosystem already) — best reasoning, longer context. | GPT-4o — cheaper for short completions, faster. | Google ADK — already in architecture diagram, multi-model. |
| **Collection granularity** | **1:1 with service types** — each dropdown value = one collection. Simple, ships fast. | Hierarchical — "Skilled Nursing → Wound Care", "Skilled Nursing → Medication Management". More flexible, more complex data model. | Tag-based — items belong to multiple collections via tags. Most flexible, hardest to build. |
| **knowledge_agent_svc** | **Separate microservice (:8011)** — clean separation, own Kafka consumer, own LangGraph env. More boilerplate. | Fold into slack_svc — fewer services to run, but mixes Slack I/O with AI workload (latency-sensitive vs. compute-heavy). | Fold into mcp_gateway — reuse existing MCP/ADK infra. |
| **File storage** | **Local filesystem** (`uploads/` dir, gitignored) — simplest for v1. | S3/GCS bucket — production-ready, scalable. Needs AWS/GCP creds. | PostgreSQL `BYTEA` — no filesystem, but large files bloat the DB. |

---

## 9. Data Model (Draft)

```sql
-- knowledge_schema (managed by knowledge_svc alembic)

CREATE TABLE knowledge_schema.collections (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,        -- "Personal Care & Companionship"
    slug            VARCHAR(255) NOT NULL UNIQUE,  -- "personal-care-companionship"
    service_type    VARCHAR(100),                  -- FK-ish to appointment.service_type
    description     TEXT,
    icon_emoji      VARCHAR(10) DEFAULT '📚',
    item_count      INT DEFAULT 0,                 -- denormalized for the grid view
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE knowledge_schema.collection_items (
    id                  SERIAL PRIMARY KEY,
    collection_id       INT NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    item_type           VARCHAR(20) NOT NULL,       -- 'document', 'announcement', 'link', 'note'
    title               VARCHAR(255) NOT NULL,
    content_text        TEXT,                        -- extracted/scraped/authored text
    source_url          VARCHAR(2048),               -- for links
    file_path           VARCHAR(512),                -- for uploaded documents
    file_size_bytes     BIGINT,
    mime_type           VARCHAR(100),
    chunk_count         INT DEFAULT 0,               -- denormalized
    created_by_user_id  INT,
    created_at          TIMESTAMPTZ DEFAULT now(),
    updated_at          TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE knowledge_schema.collection_chunks (
    id              SERIAL PRIMARY KEY,
    item_id         INT NOT NULL REFERENCES collection_items(id) ON DELETE CASCADE,
    collection_id   INT NOT NULL REFERENCES collections(id),
    chunk_index     INT NOT NULL,
    chunk_text      TEXT NOT NULL,
    embedding       VECTOR(1536),                    -- pgvector; dim matches embedding model
    token_count     INT,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX ix_chunks_collection ON knowledge_schema.collection_chunks(collection_id);
CREATE INDEX ix_chunks_embedding ON knowledge_schema.collection_chunks
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

---

## 10. LangGraph Flow Design

```
                    ┌───────────────────┐
                    │   START            │
                    │   (appointment.    │
                    │    claimed event)  │
                    └────────┬──────────┘
                             │
                             ▼
                    ┌───────────────────┐
                    │ fetch_appointment  │───► appointment_svc HTTP
                    │                   │      GET /appointments/{id}
                    │ outputs:          │      → service_type, member_id,
                    │  appointment{}    │        requested_date, notes
                    └────────┬──────────┘
                             │
                             ▼
                    ┌───────────────────┐
                    │ fetch_member      │───► member_svc HTTP + visit_mgmt HTTP
                    │ _history          │      GET /members/{id}
                    │                   │      GET /visits?member_id={id}&limit=3
                    │ outputs:          │
                    │  member_history[] │
                    └────────┬──────────┘
                             │
                             ▼
                    ┌───────────────────┐
                    │ rag_retrieve      │───► knowledge_svc HTTP
                    │                   │      POST /search
                    │ query = f"What    │      {collection_slug, query, top_k=5}
                    │ should a field    │
                    │ officer know      │
                    │ before a          │
                    │ {service_type}    │
                    │ visit?"           │
                    │                   │
                    │ outputs:          │
                    │  rag_results[]    │
                    └────────┬──────────┘
                             │
                             ▼
                    ┌───────────────────┐
                    │ synthesize        │───► LLM API (Claude / GPT-4o)
                    │ _briefing         │
                    │                   │      system_prompt +
                    │ inputs:           │      rag_chunks +
                    │  appointment      │      member_history
                    │  member_history   │
                    │  rag_results      │      → 3-paragraph briefing
                    │                   │
                    │ outputs:          │
                    │  briefing_text    │
                    └────────┬──────────┘
                             │
                             ▼
                    ┌───────────────────┐
                    │ post_to_slack     │───► shared/slack.py
                    │                   │      post_message(
                    │ thread_ts =       │        channel=...,
                    │  slack_message_ts │        text=briefing_text,
                    │ from the claim    │        thread_ts=slack_message_ts
                    │ event payload     │      )
                    └────────┬──────────┘
                             │
                             ▼
                    ┌───────────────────┐
                    │       END         │
                    └───────────────────┘
```

---

## 11. Slack Threading UX

After a claim, the Slack thread looks like this:

```
┌─────────────────────────────────────────────────┐
│ 🟢 In-Home-Care Bot                             │
│ Appointment #42 — claimed                        │
│ Claimed by: @field_officer_maria                 │
│ Service: Personal Care & Companionship           │
│ When: 2026-04-15 (Morning)                       │
├─────────────────────────────────────────────────┤
│ 💡 Thread: 2 replies                             │
│                                                  │
│ 🤖 In-Home-Care Bot  (auto-reply, 2s later)     │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│ *Care briefing — Personal Care & Companionship*  │
│                                                  │
│ 🔴 *Safety first*: per the Hygiene Guidelines    │
│ (updated Apr 10), always wear gloves during      │
│ personal care tasks. Sanitize hands before and   │
│ after each visit.                                │
│                                                  │
│ 👤 *Member M-42 notes*: 2 prior visits. Last     │
│ visit (Apr 3) noted "prefers morning routines    │
│ before 9 AM" and "allergic to latex gloves —     │
│ use nitrile."                                    │
│                                                  │
│ 📢 *Recent announcement*: the medication         │
│ reminder checklist was updated on Apr 8 —        │
│ confirm the member's schedule before starting.   │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│ _Sources: Hygiene Guidelines v4, Visit V-301     │
│ notes, Medication Reminder Checklist v2_         │
│                                                  │
│ 👩‍⚕️ @field_officer_maria                         │
│ What are the mobility restrictions for this      │
│ member?                                          │
│                                                  │
│ 🤖 In-Home-Care Bot                              │
│ Based on Visit V-301 (Apr 3): the member uses    │
│ a walker for indoor movement. No stairs — the    │
│ bedroom is on the ground floor. Assist with      │
│ transfers to/from the wheelchair for outdoor     │
│ appointments.                                    │
│ _Source: Visit V-301 care notes_                 │
└─────────────────────────────────────────────────┘
```

---

## 12. What Makes This a Moat

### Glean is horizontal. This is vertical.

Glean indexes Google Drive, Slack, Confluence, Jira — everything, for
everyone. That breadth is its strength for large enterprises but its
weakness for domain depth. Glean doesn't understand what a "Personal
Care & Companionship" visit means, doesn't know that latex-allergy
preferences belong in the briefing, doesn't know to cite the most
recent compliance update first.

### The compounding data advantage

Every document uploaded, every briefing generated, every Q&A answered
makes the knowledge base smarter for the *next* field officer claiming
the *same* service type. Over time:

- The RAG retrieval learns which chunks are most often cited in
  briefings → re-rank future retrievals
- The Q&A history reveals knowledge gaps → admin sees "field officers
  keep asking about medication interactions for Skilled Nursing but
  there's no document for that" → uploads one → gap closed
- The briefing quality improves because the LLM prompt can include
  "previous briefings for this service type were rated helpful by X%
  of field officers" (future: thumbs-up/down on the Slack reply)

### The workflow lock-in

The briefing appears *in the Slack thread the field officer is already
reading*. They don't have to open a browser, log into a portal, or
remember a search URL. The knowledge base is invisible infrastructure
— the user experience is "I claimed an appointment and a smart
briefing appeared." That's the stickiest possible integration point.

### Network effect within the organization

As more field officers use the platform:

- More questions are asked → more Q&A pairs are generated → the
  knowledge base gets richer
- More visits are completed → more visit notes are recorded → the
  member history context in briefings gets deeper
- More documents are uploaded by admin → more chunks are indexed →
  RAG retrieval quality improves
- The org can't switch to a competitor without losing all of this
  accumulated context

---

## 13. Open Questions

Things to decide before or during implementation:

1. **Collection seeding source**: hard-coded list of service types, or
   query the appointments table for distinct values? (Hard-coded is
   more predictable for v1.)

2. **OCR pipeline**: synchronous (block the upload until OCR +
   chunking + embedding finishes) or async (upload returns immediately,
   indexing happens via Kafka `item.created` consumer)? Async is
   better UX for large PDFs but adds complexity.

3. **Embedding cost control**: embed on every item save, or batch
   nightly? Per-save is fresher; batch is cheaper. For v1 with a small
   knowledge base, per-save is fine.

4. **LLM latency budget**: the briefing should appear in the Slack
   thread within 2–5 seconds of the claim. Claude Sonnet is ~1–2s for
   a 3-paragraph response; Opus is ~5–10s. GPT-4o-mini is ~0.5s.
   Pick the model that fits the latency budget.

5. **Multi-tenancy**: right now there's one tenant (`member-portal`).
   If this becomes a multi-org SaaS, collections need an `org_id`
   column and the VectorDB queries need org-scoped filtering. Not
   hard to add but affects the data model.

6. **Feedback loop**: should the Slack briefing have a 👍/👎 reaction
   prompt? That signal could feed back into retrieval re-ranking and
   prompt tuning. Very high value, modest implementation cost.

7. **Security boundary**: who can upload to a collection? Admin only
   (current design), or also field officers (crowdsourced knowledge)?
   Crowdsourced is richer but needs moderation.

8. **Offline access**: field officers in rural areas may not have
   reliable internet during the visit. Should the briefing be
   pre-cached on the mobile app? That's a Phase 5+ feature but worth
   considering in the data model.

---

---

## 14. Research Insights — Papers to Incorporate

Two arxiv papers directly inform the architecture. Key techniques
worth stealing for Phase 2–3.

### 14.1 EICopilot (Baidu, arxiv 2501.13746) — Query Masking for Intent-Based RAG

**Paper**: deployed at scale on Baidu Enterprise Search (5,000 DAU,
hundreds of millions of graph nodes). Core insight: when matching a
user's natural-language query against a bank of example queries for
few-shot RAG retrieval, **mask the entity names first** so the
similarity search matches on *intent structure*, not surface-level
entity overlap.

**How it applies to our knowledge base**:

When a field officer asks "What should I know before a Personal Care
visit?", the naive RAG approach embeds that string and matches against
chunks that mention "Personal Care". With query masking, we replace
"Personal Care" with `<SERVICE_TYPE>`, so the query becomes "What
should I know before a `<SERVICE_TYPE>` visit?". Now the vector search
finds structurally similar queries from ALL collections — e.g. a Skilled
Nursing FAQ that says "always check medication schedule before a
`<SERVICE_TYPE>` visit" — which is highly relevant but would score low
without masking because the entity name doesn't match.

**Implementation cost**: ~10 lines in the RAG search endpoint. Before
embedding the query, regex-replace known service-type names with a
generic token. Reverse-substitute in the results before showing the
user.

**Their results**: execution correctness went from 17–41% (zero-shot)
to 82–84% (masked + top-5 examples). Syntax errors halved.

**Also steal**:

- **Reflection loop**: if the LangGraph briefing agent generates a
  response the LLM flags as low-confidence, re-retrieve with a
  reformulated query and try again. Add as an optional conditional
  edge in the LangGraph state graph between `synthesize_briefing` and
  `rag_retrieve` — loops at most once, costs one extra LLM call on
  low-confidence responses.
- **Seed dataset**: curate 20–30 "gold" field-officer questions per
  service type (offline, by an admin or domain expert). Embed them and
  use as the few-shot example pool in the LLM prompt. This is their
  "offline phase" and is the single highest-ROI investment for RAG
  quality.

### 14.2 LiveVectorLake (arxiv 2601.05270) — Temporal Vector Lake for Mutable Enterprise Knowledge

**Paper**: addresses the gap between "batch re-index everything" and
"real-time incremental update" for RAG over mutable document corpora.
Core architecture: dual-tier storage (hot Milvus/vector index for
current chunks, cold Delta Lake/Parquet for full version history) with
content-addressable chunk deduplication via SHA-256 hashing.

**How it applies to our knowledge base**:

Healthcare compliance requires knowing "what information was available
to the field officer at the time of the visit" — not just the current
state of the knowledge base. When an admin updates a care protocol PDF:

1. The old chunks shouldn't disappear from the audit trail.
2. Only the paragraphs that actually changed should be re-embedded
   (saves embedding API cost).
3. The RAG query for a *current* briefing should see the new version;
   a compliance audit query for a *past* visit should see the version
   that existed at visit time.

**Implementation — 3 columns added to `collection_chunks`**:

```sql
ALTER TABLE knowledge_schema.collection_chunks ADD COLUMN
  content_hash  CHAR(64)       NOT NULL,  -- SHA-256 of chunk_text
  valid_from    TIMESTAMPTZ    NOT NULL DEFAULT now(),
  valid_until   TIMESTAMPTZ;              -- NULL = current
```

- **On item update**: compute chunk hashes for the new version.
  For each hash that already exists (unchanged paragraph), do nothing.
  For new/changed hashes, INSERT with `valid_from = now()`. For
  removed hashes, UPDATE `valid_until = now()` on the old rows.
- **Current RAG query**: `WHERE valid_until IS NULL` → only active
  chunks, keeps the cosine-similarity index small and fast.
- **Historical/compliance query**: `WHERE valid_from <= :visit_date
  AND (valid_until IS NULL OR valid_until > :visit_date)` → exact
  point-in-time knowledge reconstruction.

**Their results**:

| Metric | Before | After |
|---|---|---|
| Content re-processed on update | 85–95% | 10–15% |
| Current query latency (p50) | — | 65 ms |
| Historical query latency (p50) | — | 1.2 s |
| Hot-tier chunk reduction | — | 90% fewer active chunks |
| Temporal accuracy | — | 100% (zero temporal leakage) |

**Also steal**:

- **Deterministic CDC**: hash each chunk at ingest time. If the hash
  matches an existing row, skip the embedding API call entirely. Their
  system reduced change detection from ~100 ms DB queries to <1 ms
  in-memory hash lookups.
- **Temporal query routing**: add a `mode` parameter to the search
  API (`mode=current` vs `mode=historical&as_of=2026-04-01`). The
  briefing agent always uses `current`; a future compliance agent uses
  `historical` with the visit date.

### 14.3 Combined impact on our Phase 2 data model

Incorporating both papers, the `collection_chunks` table becomes:

```sql
CREATE TABLE knowledge_schema.collection_chunks (
    id              SERIAL PRIMARY KEY,
    item_id         INT NOT NULL REFERENCES collection_items(id) ON DELETE CASCADE,
    collection_id   INT NOT NULL REFERENCES collections(id),
    chunk_index     INT NOT NULL,
    chunk_text      TEXT NOT NULL,
    embedding       VECTOR(1536),
    content_hash    CHAR(64) NOT NULL,          -- LiveVectorLake: dedup + CDC
    valid_from      TIMESTAMPTZ NOT NULL DEFAULT now(),  -- LiveVectorLake: temporal
    valid_until     TIMESTAMPTZ,                -- NULL = current; set on update
    token_count     INT,
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- Only index CURRENT chunks for fast cosine similarity
CREATE INDEX ix_chunks_active_embedding ON knowledge_schema.collection_chunks
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100)
    WHERE valid_until IS NULL;

-- Fast hash-based dedup lookup
CREATE INDEX ix_chunks_content_hash ON knowledge_schema.collection_chunks(content_hash);
```

And the RAG search function adds **query masking** (EICopilot) before
embedding:

```python
def search(collection_slug: str, query: str, top_k: int = 5,
           mode: str = "current", as_of: datetime | None = None):
    # EICopilot: mask service-type names for intent matching
    masked_query = mask_service_types(query)
    query_embedding = embed(masked_query)

    # LiveVectorLake: temporal filtering
    if mode == "current":
        where = "valid_until IS NULL"
    else:
        where = f"valid_from <= '{as_of}' AND (valid_until IS NULL OR valid_until > '{as_of}')"

    results = vector_search(
        embedding=query_embedding,
        collection_id=collection_id,
        where=where,
        top_k=top_k,
    )
    # Unmask service-type names in results before returning
    return unmask_results(results, collection_slug)
```

---

---

## 15. Multi-Jurisdiction Knowledge Scoping

### 15.1 The problem

A care protocol for "Personal Care & Companionship" in California is
literally different from Texas. State-level differences include:

- **Scope-of-practice laws** — what a home health aide is legally
  allowed to do varies by state (e.g. medication administration is
  allowed in some states, prohibited in others)
- **Medicaid/EVV mandates** — Electronic Visit Verification rules,
  billing codes, and documentation requirements are state-specific
- **Aide certification requirements** — training hours, continuing
  education, background check rules
- **Local health department regulations** — county-level reporting,
  infection control, emergency protocols
- **Payer-specific rules** — different insurance carriers have
  different coverage rules, prior-auth requirements, documentation
  standards

If the knowledge base serves a single org in one state, this doesn't
matter. The moment it serves multiple states or multiple customer
orgs, every RAG query must be jurisdiction-aware or it will surface
wrong / non-compliant information.

### 15.2 How industry SaaS companies solve this

Three patterns, all composable:

#### Pattern 1: Hierarchical knowledge scoping (most common)

Used by **Epic**, **PointClickCare**, **Veeva Vault**, and
**ServiceNow**. Knowledge is organized in layers that cascade like
CSS — more specific layers override or supplement less specific ones:

```
Global (universal safety protocols, WHO guidelines)
  └── Country / Federal (US: CMS Conditions of Participation, HIPAA rules)
      └── State (CA, TX, NY — state licensing, Medicaid rules, EVV mandates)
          └── Region / County (optional — local health dept rules, rural vs urban)
              └── Organization (customer-specific SOPs, internal policies)
                  └── Service Type (our existing collections)
```

At query time, the RAG filter says: "give me chunks that apply to
Global + US federal + California + this org + this service type."
A field officer in Texas sees Texas-specific rules; one in California
sees California's. Both see the federal CMS baseline. The most
specific match ranks highest in the results.

#### Pattern 2: Geo-tagged documents with jurisdiction filtering

Used by **Salesforce Knowledge** ("data categories"),
**Veeva Vault** ("country/region" metadata), and compliance-heavy SaaS
like **Avalara** (tax rules by jurisdiction). Every document is tagged
with the jurisdictions it applies to:

```
Document: "California Home Health Aide Scope of Practice"
  → jurisdictions: [US, US-CA]
  → service_types: [personal-care, skilled-nursing, home-health-aide]

Document: "CMS Conditions of Participation (federal)"
  → jurisdictions: [US]
  → service_types: [*]  (applies to all)

Document: "Acme Home Care — Infection Control SOP"
  → jurisdictions: [US, US-CA, US-TX]  (Acme operates in CA + TX)
  → service_types: [*]
  → org_id: acme-home-care
```

The VectorDB query adds a metadata filter:
`WHERE jurisdiction IN ('US', 'US-CA') AND collection_id = :svc_type`.
Only applicable docs surface in the briefing.

#### Pattern 3: Tenant-scoped knowledge with shared base inheritance

Used by every multi-tenant SaaS (**Salesforce**, **ServiceNow**,
**Glean**). Each customer org gets its own namespace but inherits from
a shared "base" that the platform vendor maintains:

```
Platform-maintained base (you maintain this):
  → Federal regulations, universal protocols, best practices
  → Updated centrally — all customers see the update immediately
  → This is the subscription value: "we track regulatory changes
    so you don't have to"

Customer-specific layer (each org uploads their own):
  → Their internal SOPs, their preferred checklists, their training
    videos, their medication lists
  → Only visible to their users
  → This is the switching cost: they've uploaded their institutional
    knowledge, it's indexed, their field staff rely on it daily

Combined at query time:
  → RAG search unions both layers
  → Customer-specific docs rank higher (more specific = more relevant)
  → Platform docs fill gaps the customer hasn't covered
```

### 15.3 Real-world validation

| Company | Vertical | How they scope knowledge | Pricing signal |
|---|---|---|---|
| **PointClickCare** | Long-term / post-acute care | State-specific assessment forms, compliance rules, regulatory reporting. Each facility tagged with its state. | $5–15/bed/month |
| **MatrixCare / Brightree** | Home health + hospice | State-specific EVV rules, OASIS assessment templates, payer-specific billing rules. | $3–10/user/month |
| **Veeva Vault** | Pharma / life sciences | Country-level regulatory content, automatic jurisdiction filtering, audit trails per region. | $50K+/year enterprise |
| **Salesforce Knowledge** | Horizontal, used in healthcare | "Data categories" for geography, department, product — filter articles by category at query time. | Built into Service Cloud ($150+/user/month) |
| **Glean** | Horizontal enterprise search | Inherits permissions from source systems (Google Drive, Confluence, etc.). No explicit jurisdiction model — relies on ACLs. | $10–25/user/month |

### 15.4 Proposed data model changes

These columns added to the Phase 1 data model. Designed so a
single-state v1 deployment works without setting any of them (all
defaults are permissive), but a multi-state / multi-tenant deployment
can scope everything correctly.

```sql
-- Scoping on collections (coarse-grained: "this collection is for CA orgs")
ALTER TABLE knowledge_schema.collections ADD COLUMN
    org_id       VARCHAR(100) NOT NULL DEFAULT 'platform',
    -- 'platform' = shared base maintained by us
    -- 'acme-home-care' = customer-specific
    jurisdiction VARCHAR(20);
    -- NULL = global (applies everywhere)
    -- 'US'    = US federal
    -- 'US-CA' = California
    -- 'US-TX' = Texas
    -- ISO 3166-2 codes for consistency

-- Scoping on items (fine-grained: "this document applies to CA + TX")
ALTER TABLE knowledge_schema.collection_items ADD COLUMN
    jurisdictions TEXT[],
    -- NULL or empty = global (applies everywhere)
    -- {'US', 'US-CA'} = federal + California
    -- Postgres array enables && (overlap) operator for fast filtering
    org_id        VARCHAR(100) NOT NULL DEFAULT 'platform';
```

### 15.5 How the RAG query changes

```python
def search(
    collection_slug: str,
    query: str,
    top_k: int = 5,
    *,
    org_id: str = "platform",
    state: str | None = None,       # e.g. "US-CA"
    mode: str = "current",
    as_of: datetime | None = None,
):
    # EICopilot: mask service-type names for intent matching
    masked_query = mask_service_types(query)
    query_embedding = embed(masked_query)

    # Build the jurisdiction filter chain
    # Always include: global (NULL) + platform base
    # If state is set: also include US federal + that state
    jurisdictions = ["NULL"]  # global
    if state:
        country = state.split("-")[0]  # "US" from "US-CA"
        jurisdictions.extend([country, state])

    # LiveVectorLake: temporal filtering
    if mode == "current":
        temporal = "AND c.valid_until IS NULL"
    else:
        temporal = f"AND c.valid_from <= '{as_of}' AND (c.valid_until IS NULL OR c.valid_until > '{as_of}')"

    results = db.execute(f"""
        SELECT c.chunk_text, c.embedding <=> :query_embedding AS score,
               i.title, i.item_type, col.name AS collection_name,
               i.org_id, i.jurisdictions
        FROM knowledge_schema.collection_chunks c
        JOIN knowledge_schema.collection_items i ON i.id = c.item_id
        JOIN knowledge_schema.collections col ON col.id = c.collection_id
        WHERE col.slug = :collection_slug
          -- Tenant scoping: platform base + this org's docs
          AND (i.org_id = 'platform' OR i.org_id = :org_id)
          -- Jurisdiction scoping: global + matching jurisdictions
          AND (i.jurisdictions IS NULL
               OR i.jurisdictions && :jurisdictions_array)
          -- Temporal scoping (LiveVectorLake)
          {temporal}
        ORDER BY c.embedding <=> :query_embedding
        LIMIT :top_k
    """, ...)

    return unmask_results(results, collection_slug)
```

### 15.6 Pricing and packaging implications

The hierarchical scoping model naturally maps to SaaS pricing tiers:

| Tier | What the customer gets | Who maintains it | Price signal |
|---|---|---|---|
| **Starter** | Platform base (federal + universal protocols) + their own uploads, single state | Platform base: us. Customer layer: them. | $5–10/user/month |
| **Professional** | Above + state-specific regulatory packs for their operating states (auto-updated) | State packs: us, updated within 48h of regulatory changes. | $15–25/user/month |
| **Enterprise** | Above + multi-state, multi-org, custom LangGraph workflows, compliance audit trail (temporal queries from LiveVectorLake) | Everything above + dedicated CSM. | $30–50/user/month, annual contract |

The **platform-maintained layers** (federal + state packs) are the
subscription value — customers pay because tracking 50 states' home
health regulations is a full-time job they don't want to hire for.

The **customer-specific layer** is the switching cost — once their
institutional knowledge is indexed and their field staff rely on the
daily briefings, switching means re-uploading everything and
re-training the workflow habits.

The **compliance audit trail** (temporal queries — "what knowledge
was available when this visit happened?") is the enterprise upsell —
regulated industries pay premium for defensible audit capability.

### 15.7 Implementation phasing

| Phase | Jurisdiction support | Effort |
|---|---|---|
| Phase 1 (Collections CRUD) | Add `org_id` + `jurisdiction` columns, default everything to `platform` + `NULL`. Single-state deployment works out of the box. | +30 min |
| Phase 2 (VectorDB + search) | Add `jurisdictions` array to items, `&&` filter in search query. Admin can tag items with jurisdictions on upload. | +2 hours |
| Phase 3 (LangGraph briefing) | Pass the claimed appointment's service_area → resolve to a state code → pass to RAG search as the `state` parameter. Briefings are now state-aware. | +1 hour |
| Phase 4+ (multi-tenant) | `org_id` scoping in collections + items. Each customer org sees platform base + their own uploads. Separate admin portals per org (or org switcher). | +1–2 days |

The key insight: **add the columns in Phase 1 even if you don't use
them yet.** The cost is two `DEFAULT 'platform'` / `DEFAULT NULL`
columns. The benefit is the data model doesn't have to be migrated
later when you go multi-state or multi-tenant — you just start
populating the columns.

---

---

## 16. Admin Portal — Knowledge Base Menu & Repository Model

### 16.1 Navigation hierarchy

```
Care Admin Portal (http://127.0.0.1:3002)
│
├── Dashboard
├── Appointments
├── Slack Claims
├── Visits
├── Members
├── Staff
├── Slack Integrations
│
└── Knowledge Base              ← NEW top-level nav
    │
    ├── Collections             (grid of cards, one per service type)
    │   │
    │   ├── Personal Care & Companionship
    │   │   ├── Repositories    (list of repos inside this collection)
    │   │   │   ├── Care Protocols v4        [status: indexed ✅]
    │   │   │   ├── Hygiene Guidelines 2026  [status: locked 🔒]
    │   │   │   ├── Staff Training Q2        [status: draft ✏️]
    │   │   │   └── + Create repository
    │   │   └── (collection settings: jurisdiction, description)
    │   │
    │   ├── Skilled Nursing
    │   │   └── Repositories ...
    │   │
    │   ├── Physical Therapy
    │   │   └── Repositories ...
    │   │
    │   └── Home Health Aide
    │       └── Repositories ...
    │
    └── Indexing Status          (global view of all indexing jobs)
        └── table: repo name, status, chunks indexed, last run, errors
```

### 16.2 Page-by-page UX

#### Collections grid page (`/app/knowledge-base`)

```
┌──────────────────────────────────────────────────────────────┐
│  Knowledge Base                                    + New     │
│  Collections auto-seeded from appointment service types.     │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ 🏥            │  │ 💊            │  │ 🏃            │       │
│  │ Personal Care │  │ Skilled      │  │ Physical     │       │
│  │ & Companion.  │  │ Nursing      │  │ Therapy      │       │
│  │               │  │              │  │              │       │
│  │ 4 repos       │  │ 2 repos      │  │ 1 repo       │       │
│  │ 128 chunks    │  │ 56 chunks    │  │ 12 chunks    │       │
│  │ US-CA, US-TX  │  │ US           │  │ US-CA        │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│                                                              │
│  ┌──────────────┐                                            │
│  │ 🏠            │                                            │
│  │ Home Health   │                                            │
│  │ Aide          │                                            │
│  │               │                                            │
│  │ 0 repos       │                                            │
│  │ 0 chunks      │                                            │
│  │ —             │                                            │
│  └──────────────┘                                            │
└──────────────────────────────────────────────────────────────┘
```

#### Repository list inside a collection (`/app/knowledge-base/:collectionSlug`)

```
┌──────────────────────────────────────────────────────────────┐
│  ← Back to Knowledge Base                                    │
│  Personal Care & Companionship         + Create repository   │
│  US-CA, US-TX  |  4 repositories  |  128 chunks indexed      │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Name                    │ Type     │ Items │ Status    │  │
│  ├─────────────────────────┼──────────┼───────┼───────────┤  │
│  │ Care Protocols v4       │ policies │   3   │ ✅ indexed │  │
│  │ Hygiene Guidelines 2026 │ policies │   2   │ 🔒 locked  │  │
│  │ Staff Training Q2       │ research │   5   │ ✏️ draft   │  │
│  │ Field Notes — Apr 2026  │ exprnces │   8   │ ✅ indexed │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

#### Repository detail page (`/app/knowledge-base/:collectionSlug/:repoId`)

```
┌──────────────────────────────────────────────────────────────┐
│  ← Back to Personal Care & Companionship                     │
│  Care Protocols v4                                           │
│  Type: policies  |  Status: ✅ indexed  |  128 chunks        │
│  Jurisdictions: US, US-CA                                    │
│                                                              │
│  ┌───────────── Actions ──────────────┐                      │
│  │  [Lock repository 🔒]             │  (only in draft)     │
│  │  [Publish to indexing 🚀]         │  (only when locked)  │
│  │  [Unlock ✏️]                      │  (only when locked)  │
│  │  [Re-index 🔄]                    │  (only when indexed) │
│  └────────────────────────────────────┘                      │
│                                                              │
│  ── Items ─────────────────────────── + Add item             │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Title                 │ Type          │ Size   │ Added │  │
│  ├───────────────────────┼───────────────┼────────┼───────┤  │
│  │ arrival_protocol.pdf  │ 📄 document   │ 240 KB │ Apr 8 │  │
│  │ glove_guidelines.pdf  │ 📄 document   │ 180 KB │ Apr 9 │  │
│  │ medication_checklist   │ 📝 note       │ —      │ Apr 10│  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ── Source location ──────────────────────────────────────    │
│  Local: ./knowledge_data/personal-care/care-protocols-v4/    │
│  S3:    s3://ihcp-knowledge/personal-care/care-protocols-v4/ │
│  (files in this folder are auto-discovered on publish)       │
│                                                              │
│  ── Indexing history ─────────────────────────────────────    │
│  │ Run        │ Status  │ Chunks │ Duration │ Errors │       │
│  │ Apr 10 3pm │ success │ 128    │ 12s      │ 0      │       │
│  │ Apr 8 1pm  │ success │ 96     │ 9s       │ 0      │       │
└──────────────────────────────────────────────────────────────┘
```

### 16.3 Repository item types

Each repository has a primary *type* that describes the kind of
knowledge it holds. Items within the repository can be mixed, but
the type helps admins organize and helps the RAG retrieval rank
results (a "policy" document may rank higher than an "experience"
note for compliance-sensitive queries).

| Type slug | Label | Icon | Description | Typical content |
|---|---|---|---|---|
| `announcements` | Announcements | 📢 | Time-sensitive policy updates, regulatory changes | "Starting May 1, all CA aides must complete 4h refresher training" |
| `notes` | Notes | 📝 | Short-form clinical tips, Q&A from experienced staff | "For diabetic members, always check blood sugar before meal prep" |
| `policies` | Policies | 📋 | SOPs, compliance documents, care protocols | "Infection Control SOP v4.2.pdf" |
| `knowledgebases` | Knowledge Bases | 📚 | Structured reference material, FAQs, decision trees | "Wound care classification guide", "Fall risk assessment matrix" |
| `research` | Research | 🔬 | Clinical studies, evidence-based guidelines, training materials | "CDC hand hygiene guidelines", "Best practices for dementia care" |
| `experiences` | Experiences | 💡 | Field officer lessons learned, case studies, peer tips | "What I learned from 100 Personal Care visits" |
| `others` | Others | 📎 | Anything that doesn't fit the above categories | Links, miscellaneous references |

### 16.4 Repository lifecycle

```
  ┌──────┐     lock      ┌──────┐    publish     ┌──────────┐    Airflow    ┌─────────┐
  │ DRAFT│ ──────────► │LOCKED│ ────────────► │PUBLISHING│ ──────────► │ INDEXED │
  │  ✏️   │              │  🔒  │               │    🔄     │   success    │   ✅    │
  └──────┘              └──────┘               └──────────┘              └─────────┘
     ▲                     │                        │                         │
     │        unlock       │                        │ failure                 │
     └─────────────────────┘                        │                    re-index
                                               ┌────▼────┐                   │
                                               │  FAILED │                   │
                                               │    ❌   │◄──────────────────┘
                                               └─────────┘      (re-index after fixing)
```

**States explained:**

| State | Editable? | What happens | Admin action |
|---|---|---|---|
| `draft` ✏️ | Yes — add/edit/remove items, change metadata | Nothing is indexed; the repo is work-in-progress | Lock when ready |
| `locked` 🔒 | No — items and metadata are frozen | Ready for review / approval before publishing | Publish to indexing, or unlock to go back to draft |
| `publishing` 🔄 | No | Kafka message sent, Airflow DAG is processing | Wait (status auto-updates via polling or webhook) |
| `indexed` ✅ | No | All chunks are in the VectorDB, available to RAG queries | Re-index (triggers a fresh Airflow run), or unlock → draft to edit |
| `failed` ❌ | No | Airflow DAG failed (OCR error, embedding API down, etc.) | Fix the issue, then re-index |

**Why lock before publish?** Prevents the situation where an admin
edits a document while Airflow is mid-indexing, which would create
a race between the old and new content. Lock ensures the content is
frozen for the duration of the indexing pipeline. Unlock after
indexing to start the next edit cycle.

### 16.5 Source locations — folder / S3

Each repository has a **source path** that tells the indexing pipeline
where to find the raw files. Two modes:

| Mode | Path format | When to use |
|---|---|---|
| **Local folder** | `./knowledge_data/{collection-slug}/{repo-slug}/` | Local dev, small teams, quick iteration |
| **S3 bucket** | `s3://{bucket}/{collection-slug}/{repo-slug}/` | Production, multi-machine, durable storage |

**Auto-discovery**: when the admin clicks "Publish to indexing", the
pipeline scans the source path for all files (PDFs, DOCXes, TXTs,
Markdown, images) and processes each one. Files already indexed (by
content hash, per LiveVectorLake's dedup strategy) are skipped.

**Folder structure convention**:

```
knowledge_data/                                ← gitignored
├── personal-care-companionship/
│   ├── care-protocols-v4/
│   │   ├── arrival_protocol.pdf
│   │   ├── glove_guidelines.pdf
│   │   └── medication_checklist.md
│   └── hygiene-guidelines-2026/
│       ├── hygiene_update_apr2026.pdf
│       └── hand_washing_poster.png
├── skilled-nursing/
│   └── wound-care-protocols/
│       └── wound_classification_guide.pdf
└── ...
```

**S3 equivalent** (same structure, different root):

```
s3://ihcp-knowledge-prod/
├── personal-care-companionship/
│   ├── care-protocols-v4/
│   │   └── ...
│   └── ...
└── ...
```

The source mode is configured per repository (or globally via env
var `KNOWLEDGE_SOURCE_MODE=local|s3` with `KNOWLEDGE_S3_BUCKET` for
the bucket name).

### 16.6 Kafka → Airflow async indexing pipeline

```
Admin clicks "Publish to indexing"
    │
    ▼
┌──────────────────────────────────────────────────────────────┐
│ API Gateway                                                   │
│ POST /api/admin/knowledge/repositories/{id}/publish           │
│   1. Verify repo is in LOCKED state                           │
│   2. Update status → PUBLISHING                               │
│   3. Publish Kafka event:                                     │
│      topic: knowledge.indexing                                │
│      payload: {                                               │
│        event_type: "repository.publish",                      │
│        repository_id: 42,                                     │
│        collection_id: 7,                                      │
│        collection_slug: "personal-care-companionship",        │
│        source_path: "./knowledge_data/personal-care/...",     │
│        source_mode: "local",                                  │
│        org_id: "platform",                                    │
│        jurisdictions: ["US", "US-CA"],                        │
│        occurred_at: "2026-04-11T..."                          │
│      }                                                        │
│   4. Return 202 Accepted                                      │
└──────────────────────────────────────────────────────────────┘
    │
    │ Kafka topic: knowledge.indexing
    ▼
┌──────────────────────────────────────────────────────────────┐
│ Apache Airflow                                                │
│ DAG: knowledge_indexing_dag                                   │
│ Trigger: KafkaConsumer sensor on knowledge.indexing            │
│                                                               │
│ Task 1: discover_files                                        │
│   Scan source_path for all files                              │
│   Output: list of file paths + mime types                     │
│                                                               │
│ Task 2: extract_text (parallel per file)                      │
│   For each file:                                              │
│     PDF/DOCX/image → call document_intelligence_svc OCR       │
│     Markdown/TXT → read directly                              │
│   Output: list of (file_path, extracted_text)                 │
│                                                               │
│ Task 3: chunk_and_hash                                        │
│   For each extracted text:                                    │
│     Recursive character splitter (512 tokens, 50 overlap)     │
│     SHA-256 hash each chunk (LiveVectorLake dedup)            │
│   Output: list of (chunk_text, content_hash, chunk_index)     │
│                                                               │
│ Task 4: dedup_and_embed                                       │
│   For each chunk:                                             │
│     Check content_hash against existing chunks in DB           │
│     If hash exists AND valid_until IS NULL → skip (unchanged) │
│     If hash is new → embed via OpenAI text-embedding-3-small  │
│   For chunks that disappeared (old hash not in new set):      │
│     UPDATE valid_until = now() (LiveVectorLake soft-delete)   │
│   Output: list of (chunk_text, embedding, content_hash)       │
│                                                               │
│ Task 5: store_in_vectordb                                     │
│   INSERT new chunks into collection_chunks                    │
│   (with collection_id, item_id, content_hash, valid_from)     │
│   Update repository: status → INDEXED, chunk_count = N        │
│                                                               │
│ Task 6: notify_completion                                     │
│   Publish Kafka event:                                        │
│     topic: knowledge.indexing                                 │
│     payload: {                                                │
│       event_type: "repository.indexed",                       │
│       repository_id: 42,                                      │
│       chunks_indexed: 128,                                    │
│       chunks_skipped: 42,  (unchanged, deduped)               │
│       chunks_expired: 3,   (old versions soft-deleted)        │
│       duration_seconds: 12,                                   │
│       status: "success" | "failed",                           │
│       error: null | "embedding API returned 429"              │
│     }                                                         │
│                                                               │
│ On failure at any task:                                        │
│   Update repository status → FAILED                           │
│   Publish failure event with error details                    │
│   Airflow retries per task retry policy (3 retries, 60s wait) │
└──────────────────────────────────────────────────────────────┘
    │
    │ Kafka topic: knowledge.indexing (completion event)
    ▼
┌──────────────────────────────────────────────────────────────┐
│ knowledge_svc (or api_gateway)                                │
│ Consumer: listens for repository.indexed / repository.failed  │
│   → Updates repository status in DB                           │
│   → Admin portal polls /repositories/{id} and sees the new    │
│     status without a page refresh (or uses a WebSocket push)  │
└──────────────────────────────────────────────────────────────┘
```

### 16.7 Why Airflow (not inline in knowledge_svc)

| Concern | Inline (knowledge_svc) | Airflow |
|---|---|---|
| **Long-running** | Blocks the API thread; 50-page PDF OCR + embedding takes 30–60s | Async worker, API returns 202 immediately |
| **Retries** | Hand-rolled retry logic | Built-in per-task retry policy with exponential backoff |
| **Monitoring** | Custom logging | Airflow UI shows task status, duration, logs, gantt chart |
| **Parallelism** | Single-threaded GIL | Airflow can fan-out `extract_text` across multiple workers |
| **Scheduling** | Not possible | Future: nightly re-index DAG, scheduled S3 sync |
| **Already in stack** | — | ✅ `DevOps/Local/Airflow/docker-compose.yml` already exists |

### 16.8 Updated data model (replaces Section 9)

```sql
-- knowledge_schema (managed by knowledge_svc alembic)

CREATE TABLE knowledge_schema.collections (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    slug            VARCHAR(255) NOT NULL UNIQUE,
    service_type    VARCHAR(100),
    description     TEXT,
    icon_emoji      VARCHAR(10) DEFAULT '📚',
    org_id          VARCHAR(100) NOT NULL DEFAULT 'platform',
    jurisdiction    VARCHAR(20),
    repo_count      INT DEFAULT 0,
    total_chunks    INT DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE knowledge_schema.repositories (
    id              SERIAL PRIMARY KEY,
    collection_id   INT NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    name            VARCHAR(255) NOT NULL,
    slug            VARCHAR(255) NOT NULL,
    repo_type       VARCHAR(30) NOT NULL DEFAULT 'others',
    -- 'announcements','notes','policies','knowledgebases',
    -- 'research','experiences','others'
    status          VARCHAR(20) NOT NULL DEFAULT 'draft',
    -- 'draft','locked','publishing','indexed','failed'
    description     TEXT,
    source_mode     VARCHAR(10) DEFAULT 'local',    -- 'local' | 's3'
    source_path     VARCHAR(1024),
    -- local: ./knowledge_data/{collection-slug}/{repo-slug}/
    -- s3:    s3://bucket/{collection-slug}/{repo-slug}/
    org_id          VARCHAR(100) NOT NULL DEFAULT 'platform',
    jurisdictions   TEXT[],
    item_count      INT DEFAULT 0,
    chunk_count     INT DEFAULT 0,
    last_indexed_at TIMESTAMPTZ,
    last_error      TEXT,
    created_by_user_id INT,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now(),
    UNIQUE(collection_id, slug)
);

CREATE TABLE knowledge_schema.repository_items (
    id              SERIAL PRIMARY KEY,
    repository_id   INT NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    collection_id   INT NOT NULL REFERENCES collections(id),
    item_type       VARCHAR(20) NOT NULL,
    -- 'document','announcement','link','note','image'
    title           VARCHAR(255) NOT NULL,
    content_text    TEXT,
    source_url      VARCHAR(2048),
    file_path       VARCHAR(512),
    file_name       VARCHAR(255),
    file_size_bytes BIGINT,
    mime_type       VARCHAR(100),
    chunk_count     INT DEFAULT 0,
    org_id          VARCHAR(100) NOT NULL DEFAULT 'platform',
    jurisdictions   TEXT[],
    created_by_user_id INT,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE knowledge_schema.collection_chunks (
    id              SERIAL PRIMARY KEY,
    item_id         INT NOT NULL REFERENCES repository_items(id) ON DELETE CASCADE,
    repository_id   INT NOT NULL REFERENCES repositories(id),
    collection_id   INT NOT NULL REFERENCES collections(id),
    chunk_index     INT NOT NULL,
    chunk_text      TEXT NOT NULL,
    embedding       VECTOR(1536),
    content_hash    CHAR(64) NOT NULL,
    valid_from      TIMESTAMPTZ NOT NULL DEFAULT now(),
    valid_until     TIMESTAMPTZ,
    token_count     INT,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX ix_chunks_active_embedding
    ON knowledge_schema.collection_chunks
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100)
    WHERE valid_until IS NULL;

CREATE INDEX ix_chunks_content_hash
    ON knowledge_schema.collection_chunks(content_hash);

CREATE INDEX ix_chunks_collection
    ON knowledge_schema.collection_chunks(collection_id)
    WHERE valid_until IS NULL;

CREATE TABLE knowledge_schema.indexing_runs (
    id              SERIAL PRIMARY KEY,
    repository_id   INT NOT NULL REFERENCES repositories(id),
    status          VARCHAR(20) NOT NULL DEFAULT 'running',
    -- 'running','success','failed'
    chunks_indexed  INT DEFAULT 0,
    chunks_skipped  INT DEFAULT 0,
    chunks_expired  INT DEFAULT 0,
    duration_seconds FLOAT,
    error           TEXT,
    airflow_dag_run_id VARCHAR(255),
    started_at      TIMESTAMPTZ DEFAULT now(),
    completed_at    TIMESTAMPTZ
);
```

### 16.9 Airflow DAG sketch (Python)

```python
# dags/knowledge_indexing_dag.py

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.apache.kafka.sensors.kafka import \
    AwaitMessageTriggerEvent  # or a custom KafkaSensor
from datetime import datetime, timedelta

default_args = {
    "owner": "knowledge_svc",
    "retries": 3,
    "retry_delay": timedelta(seconds=60),
}

with DAG(
    "knowledge_indexing_dag",
    default_args=default_args,
    schedule_interval=None,  # triggered by Kafka, not on a cron
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["knowledge", "indexing", "vectordb"],
) as dag:

    def discover_files(**ctx):
        """Scan source_path for all processable files."""
        ...

    def extract_text(**ctx):
        """OCR PDFs/images via document_intelligence_svc, read text files."""
        ...

    def chunk_and_hash(**ctx):
        """Recursive character splitter + SHA-256 per chunk."""
        ...

    def dedup_and_embed(**ctx):
        """Skip unchanged chunks (hash match), embed new ones via OpenAI."""
        ...

    def store_in_vectordb(**ctx):
        """INSERT new chunks, soft-delete removed ones, update repo status."""
        ...

    def notify_completion(**ctx):
        """Publish repository.indexed event to Kafka."""
        ...

    t1 = PythonOperator(task_id="discover_files", python_callable=discover_files)
    t2 = PythonOperator(task_id="extract_text", python_callable=extract_text)
    t3 = PythonOperator(task_id="chunk_and_hash", python_callable=chunk_and_hash)
    t4 = PythonOperator(task_id="dedup_and_embed", python_callable=dedup_and_embed)
    t5 = PythonOperator(task_id="store_in_vectordb", python_callable=store_in_vectordb)
    t6 = PythonOperator(task_id="notify_completion", python_callable=notify_completion)

    t1 >> t2 >> t3 >> t4 >> t5 >> t6
```

### 16.10 Updated phase plan (incorporating repositories + Airflow)

| Phase | What ships | Scope |
|---|---|---|
| **Phase 1a** | Collections CRUD + admin grid page | Collections table + API + UI. Auto-seed from service types. |
| **Phase 1b** | Repositories CRUD + admin list/detail pages | Repositories table + API + UI. Lifecycle: draft → locked. Item upload (files stored locally). |
| **Phase 2a** | ✅ pgvector inline indexing | pgvector extension enabled. sentence-transformers embedding (384 dim). Chunks stored via BackgroundTask on Publish. Content-hash dedup. Per-engine indexing_runs tracking. |
| **Phase 2b** | Multi-strategy chunking | 4 strategies (sentence, recursive, semantic, parent_doc) stored in same table with chunk_strategy column. De-dup across strategies. |
| **Phase 2c** | RAG search API | `POST /knowledge/search` with collection scoping, multi-strategy retrieval, de-duplication, jurisdiction filtering, temporal mode, query masking. |
| **Phase 3** | LangGraph briefing agent + Slack auto-reply on Claim | `appointment.claimed` Kafka event → knowledge_agent_svc → RAG → LLM → Slack threaded reply. |
| **Phase 4** | Interactive Slack Q&A in thread | Slack Events API `message.channels` → re-run RAG with user question → threaded LLM reply. |
| **Phase 5** | S3 source mode + multi-tenant | S3 folder scanning, org_id scoping, per-customer portals. |

---

---

## 17. Multi-Strategy Chunking for RAG

### 17.1 Why one strategy is not enough

Different query types need different chunk granularities. A single
chunking strategy produces good results for some queries and garbage
for others:

| Query type | Example | Best chunk size |
|---|---|---|
| Factual lookup | "What's the BP threshold for calling the physician?" | **Small** (1-2 sentences) — precise match, minimal noise |
| Conceptual overview | "Explain the fall prevention protocol" | **Medium** (paragraph-sized, topic-grouped) — coherent context |
| Procedural how-to | "How do I do a wound dressing change?" | **Large** (full section) — complete procedure, not a fragment |
| Temporal/policy | "What changed in the April hygiene update?" | **Full item** (entire announcement) — need the whole update |

If we only store recursive chunks (400 chars), the factual query
drowns in surrounding text, and the procedural query gets cut
mid-step. Multiple strategies let the retrieval engine find the
**right granularity** for each query automatically.

### 17.2 The four strategies

All four run on the same document text, producing different chunk
sets stored in the same table with a `chunk_strategy` column:

```
┌─────────────────────────────────────────────────────────┐
│                    Same document text                    │
│                                                         │
│  SENTENCE                                               │
│  Split on ". " — one chunk per sentence.                │
│  → many small chunks (5-30 words each)                  │
│  → best for factual Q&A lookup                          │
│                                                         │
│  RECURSIVE                                              │
│  Split on \n\n → \n → ". " → " " — 200-400 tokens.    │
│  → medium chunks respecting paragraph boundaries        │
│  → best general-purpose retrieval                       │
│  → improved from the naive fixed-char splitter          │
│                                                         │
│  SEMANTIC                                               │
│  Embed each sentence. Merge adjacent sentences whose    │
│  cosine similarity > 0.75 into one chunk.               │
│  → variable-size chunks that follow topic boundaries    │
│  → best for conceptual questions                        │
│                                                         │
│  PARENT_DOC                                             │
│  Store the full item text as one chunk.                  │
│  → one big chunk per item                               │
│  → best for short items (announcements, notes)          │
│  → also used as "parent" context when a small chunk     │
│    matches but the LLM needs surrounding context        │
└─────────────────────────────────────────────────────────┘
```

### 17.3 Storage design — same table, strategy column

**NOT separate tables.** One table, one pgvector index, one query:

```sql
ALTER TABLE knowledge_schema.collection_chunks
  ADD COLUMN chunk_strategy VARCHAR(30) NOT NULL DEFAULT 'recursive';

-- The existing pgvector cosine-similarity index covers ALL strategies.
-- No schema changes beyond the one column.
```

Example rows after indexing one item with all 4 strategies:

```
id | item_id | chunk_strategy | chunk_index | chunk_text                      | embedding
1  | 42      | sentence       | 0           | "Check water temp (100-105°F)." | [0.12,...]
2  | 42      | sentence       | 1           | "Gather supplies first."        | [0.08,...]
3  | 42      | recursive      | 0           | "Check water temp ... supplies  | [0.11,...]
   |         |                |             |  ... Wash face first (no soap)" |
4  | 42      | semantic       | 0           | "Check water temp ... non-slip" | [0.10,...]
5  | 42      | parent_doc     | 0           | (entire item text as one chunk) | [0.09,...]
```

### 17.4 How retrieval uses multiple strategies

At query time, the RAG search queries ALL strategies in one SQL
statement. pgvector's cosine similarity naturally surfaces the best
match regardless of which strategy produced it:

```python
def search_knowledge(collection_id, query, top_k=10):
    query_embedding = embed(query)

    # One query, all strategies — pgvector handles the ranking
    raw_results = db.execute("""
        SELECT chunk_text, chunk_strategy, item_id,
               embedding <=> %s AS score,
               i.title AS source_title
        FROM collection_chunks c
        JOIN repository_items i ON i.id = c.item_id
        WHERE c.collection_id = %s
          AND c.valid_until IS NULL
        ORDER BY embedding <=> %s
        LIMIT %s
    """, (query_embedding, collection_id, query_embedding, top_k * 2))

    # De-duplicate overlapping chunks (see 17.5)
    deduped = deduplicate_by_containment(raw_results)

    return deduped[:top_k]
```

**No strategy selection logic needed.** The vector similarity score
naturally picks the right granularity:
- "What's the BP threshold?" → sentence chunk scores highest
  (exact match, small, precise)
- "Explain fall prevention" → recursive or semantic chunk scores
  highest (coherent paragraph)
- "What changed in April?" → parent_doc chunk scores highest
  (the full announcement)

### 17.5 De-duplication of overlapping chunks

Multiple strategies produce overlapping text from the same item.
Before sending to the LLM, remove redundancy:

```python
def deduplicate_by_containment(results):
    """If chunk A is a substring of chunk B (same item), keep only B."""
    kept = []
    for r in results:
        is_contained = False
        for other in results:
            if (other['item_id'] == r['item_id']
                and r['chunk_text'] in other['chunk_text']
                and len(other['chunk_text']) > len(r['chunk_text'])):
                is_contained = True
                break
        if not is_contained:
            kept.append(r)
    return kept
```

This ensures the LLM gets the **most complete, non-overlapping** text
blocks — e.g. if a sentence chunk matches but the recursive chunk from
the same item also appears in the top-K, the recursive one wins
(more context, same match).

### 17.6 How the LLM sees it

**The LLM never sees strategy labels.** The retrieval pipeline outputs
clean text blocks with source citations. The prompt looks like:

```
Context from knowledge base:
---
[1] Source: "Vital Signs & Assessment" (Skilled Nursing)
Adult vital sign normal ranges: BP 90/60 to 120/80 mmHg.
Pulse: 60-100 bpm. Respirations: 12-20/min...

[2] Source: "When to call the physician" (Skilled Nursing)
Call immediately if: BP >180/120 or <80/50, pulse >120 or <50...

[3] Source: "AHA Blood Pressure Categories" (link)
https://www.heart.org/...
---

Question: What's the BP threshold for calling the physician?
```

The LLM answers from the context and cites [1], [2], [3] by source
title. Which chunking strategy produced each block is irrelevant to
the LLM — it's a retrieval optimization, not an LLM input.

### 17.7 Storage math

For the current 80 seeded items:

| Strategy | Est. chunks | Rationale |
|---|---|---|
| sentence | ~400 | avg 5 sentences/item |
| recursive | ~160 | avg 2 paragraphs/item |
| semantic | ~200 | between sentence and recursive |
| parent_doc | 80 | 1 per item |
| **Total** | **~840** | |

Storage: 840 chunks × 384-dim × 4 bytes/float = **~1.3 MB**.
Negligible for pgvector (handles millions of vectors).

Embedding cost: ~4x more embeddings per item (one-time on Publish,
not per query). sentence-transformers processes ~100 chunks/sec on
CPU. For 840 chunks: **~8 seconds** total embedding time.

Query cost: unchanged. One `ORDER BY embedding <=> query LIMIT 10`
regardless of how many strategies are stored — the index covers all
rows.

### 17.8 Implementation plan

| Step | What | Effort |
|---|---|---|
| 1 | Add `chunk_strategy` column (alembic migration) | 10 min |
| 2 | Implement 4 chunking functions in `indexing.py` | 1 hour |
| 3 | Update `run_indexing_pipeline` to run all strategies per item | 30 min |
| 4 | Update Stored Chunks UI to show strategy column + filter | 20 min |
| 5 | Build `deduplicate_by_containment` for Phase 2c retrieval | 20 min |
| **Total** | | **~2 hours** |

---

## 18. Implementation Status

What has been built vs. what remains, as of 2026-04-12.

### 18.1 Completed (live + committed)

| Phase | Feature | Commit |
|---|---|---|
| **Phase 1a** | Collections CRUD + admin grid page, auto-seed 7 service types | `f6613d2` |
| **Phase 1a** | Setup Defaults: one-click seed of 25 repos + 80 items from JSON | `8882899` |
| **Phase 1a** | Tracked setup-defaults job with status card + reset | `da4c488` |
| **Phase 1b** | Repositories CRUD + lifecycle (draft → lock → publish → indexed) | `f6613d2` |
| **Phase 1b** | Repository items: notes, announcements, links + file upload | `f6613d2` |
| **Phase 1b** | Per-repository vector DB checkboxes (7 engines, env-gated) | `31cb76b` |
| **Phase 1b** | Publishing History with per-engine indexing_runs tracking | `31cb76b` |
| **Phase 1b** | Clickable indexing run detail page + stored chunks viewer | `00b8e1b` |
| **Phase 2a** | pgvector/pgvector:pg16 Docker image | `3e2c5c4` |
| **Phase 2a** | pgvector extension + collection_chunks table (vector(384)) | `3e2c5c4` |
| **Phase 2a** | Inline indexing pipeline: chunk + SHA-256 dedup + sentence-transformers embed + pgvector INSERT | `3e2c5c4` |
| **Phase 2a** | Publish button triggers real background indexing | `3e2c5c4` |
| — | knowledge_svc microservice on port 8010 | `f6613d2` |
| — | api_gateway knowledge_routes + KnowledgeClient proxy | `f6613d2` |
| — | Admin portal: Knowledge Base nav + 4 pages (collections, collection detail, repo detail, run detail) | `f6613d2` – `00b8e1b` |

### 18.2 Next to build

| Phase | Feature | Status | Effort |
|---|---|---|---|
| **Phase 2b** | Multi-strategy chunking (sentence, recursive, semantic, parent_doc) | Designed (section 17) | ~2 hours |
| **Phase 2c** | RAG search API with multi-strategy retrieval + de-dup + query masking | Designed (sections 14, 17) | ~3 hours |
| **Phase 3** | `appointment.claimed` Kafka event + LangGraph briefing agent + Slack threaded reply | Designed (sections 10, 11) | ~1 day |
| **Phase 4** | Interactive Slack Q&A (Events API `message.channels` → RAG → threaded reply) | Designed (section 7) | ~1 day |
| **Phase 5** | Airflow DAG for production indexing + S3 source mode + multi-tenant | Designed (sections 15, 16) | ~2 days |

### 18.3 Architecture decisions made

| Decision | Choice | Rationale |
|---|---|---|
| VectorDB (primary) | **pgvector** in same Postgres | Zero extra infra, same DB, proven at scale |
| Embedding model (dev) | **sentence-transformers all-MiniLM-L6-v2** (384 dim) | Free, offline, fast on CPU |
| Embedding model (prod) | OpenAI text-embedding-3-small (1536 dim) | Best quality/cost, needs API key |
| Chunking | **Multi-strategy** (4 strategies, same table) | Different queries need different granularities |
| Indexing trigger | **Inline BackgroundTask** (not Airflow yet) | Simpler, adequate for <1000 items |
| Collection granularity | **1:1 with service types** | Simple, ships fast, hierarchy later |
| Jurisdiction scoping | **org_id + jurisdictions columns** (added, unused) | Ready for multi-state/multi-tenant without migration |
| Knowledge source | **Local folder** (dev), S3 (future) | knowledge_data/ gitignored, auto-created on repo create |
| Dedup strategy | **SHA-256 content hash** per chunk (LiveVectorLake) | Skip unchanged chunks on re-index, ~90% cost reduction |
| Temporal queries | **valid_from / valid_until** on chunks (LiveVectorLake) | Point-in-time compliance queries for healthcare audit |

---

---

## 19. Multi-LLM Fan-Out, Token Economics & Observability

### 19.1 The concept

When a field officer claims an appointment, the system doesn't just
call one LLM — it **fans out the same RAG-augmented prompt to every
configured model** (Claude, GPT, Gemini, Ollama/local, Qwen, etc.),
stores every response, tracks token usage + cost per model, and
surfaces all responses in the appointment detail page so admins can
**compare model quality side-by-side**.

This turns the platform into an **LLM evaluation framework** built
into the product — not a separate tool. Every real appointment is an
evaluation datapoint. Over time, the org learns which model produces
the best briefings for which service type, at what cost.

### 19.2 Architecture

```
Appointment claimed → Kafka appointment.claimed
    │
    ▼
knowledge_agent_svc
    │
    ├─► RAG search (Phase 2c) → top chunks from pgvector
    │
    ├─► Assemble prompt (system + RAG context + member history)
    │
    ├─► Fan-out to ALL enabled models (parallel):
    │   ├─► Claude (Anthropic API)
    │   ├─► GPT-4o (OpenAI API)
    │   ├─► Gemini (Google AI / Vertex)
    │   ├─► Ollama (local, no API key)
    │   ├─► Qwen (Alibaba Cloud or local)
    │   ├─► Mistral
    │   ├─► Llama 3 (via Ollama or Groq)
    │   └─► ... (extensible)
    │
    ├─► For EACH response:
    │   ├─► Track: input_tokens, output_tokens, cost_usd, latency_ms
    │   ├─► Store in llm_responses table
    │   └─► Emit Prometheus metrics
    │
    ├─► Pick the PRIMARY response (configurable: fastest, cheapest,
    │   highest-quality model, or admin-selected default)
    │
    └─► Post PRIMARY response as Slack threaded reply
        (other responses visible in admin/support/field portals)
```

### 19.3 Model registry

A system-level config (JSON or DB table) lists every supported LLM
with its API endpoint, pricing, and enabled status:

```json
{
  "models": [
    {
      "id": "claude-sonnet-4",
      "provider": "anthropic",
      "display_name": "Claude Sonnet 4",
      "api_base": "https://api.anthropic.com/v1",
      "model_id": "claude-sonnet-4-20250514",
      "input_cost_per_1k": 0.003,
      "output_cost_per_1k": 0.015,
      "max_context_tokens": 200000,
      "enabled": true,
      "is_primary": true,
      "env_key": "ANTHROPIC_API_KEY"
    },
    {
      "id": "gpt-4o",
      "provider": "openai",
      "display_name": "GPT-4o",
      "api_base": "https://api.openai.com/v1",
      "model_id": "gpt-4o",
      "input_cost_per_1k": 0.0025,
      "output_cost_per_1k": 0.01,
      "max_context_tokens": 128000,
      "enabled": true,
      "is_primary": false,
      "env_key": "OPENAI_API_KEY"
    },
    {
      "id": "gemini-2.0-flash",
      "provider": "google",
      "display_name": "Gemini 2.0 Flash",
      "api_base": "https://generativelanguage.googleapis.com/v1",
      "model_id": "gemini-2.0-flash",
      "input_cost_per_1k": 0.0001,
      "output_cost_per_1k": 0.0004,
      "max_context_tokens": 1000000,
      "enabled": false,
      "is_primary": false,
      "env_key": "GOOGLE_AI_API_KEY"
    },
    {
      "id": "ollama-llama3",
      "provider": "ollama",
      "display_name": "Llama 3 (local via Ollama)",
      "api_base": "http://localhost:11434",
      "model_id": "llama3",
      "input_cost_per_1k": 0.0,
      "output_cost_per_1k": 0.0,
      "max_context_tokens": 8192,
      "enabled": false,
      "is_primary": false,
      "env_key": null
    },
    {
      "id": "qwen-2.5",
      "provider": "ollama",
      "display_name": "Qwen 2.5 (local via Ollama)",
      "api_base": "http://localhost:11434",
      "model_id": "qwen2.5",
      "input_cost_per_1k": 0.0,
      "output_cost_per_1k": 0.0,
      "max_context_tokens": 32768,
      "enabled": false,
      "is_primary": false,
      "env_key": null
    },
    {
      "id": "mistral-large",
      "provider": "mistral",
      "display_name": "Mistral Large",
      "api_base": "https://api.mistral.ai/v1",
      "model_id": "mistral-large-latest",
      "input_cost_per_1k": 0.002,
      "output_cost_per_1k": 0.006,
      "max_context_tokens": 128000,
      "enabled": false,
      "is_primary": false,
      "env_key": "MISTRAL_API_KEY"
    }
  ]
}
```

Admin UI: a **Model Registry** page showing all models with
enable/disable toggles, cost display, and a "Set as primary" button.
Disabled models are skipped during fan-out. Models without their
`env_key` set in `.env.local` are greyed out (same pattern as vector
DB checkboxes).

### 19.4 Data model — llm_responses

```sql
CREATE TABLE knowledge_schema.llm_responses (
    id                  SERIAL PRIMARY KEY,
    appointment_id      INT NOT NULL,
    model_id            VARCHAR(50) NOT NULL,
    provider            VARCHAR(30) NOT NULL,
    display_name        VARCHAR(100),

    -- Prompt
    system_prompt       TEXT,
    user_prompt         TEXT NOT NULL,
    rag_chunks_used     INT,
    rag_chunk_ids       INT[],

    -- Response
    response_text       TEXT NOT NULL,
    finish_reason       VARCHAR(30),

    -- Token economics
    input_tokens        INT NOT NULL DEFAULT 0,
    output_tokens       INT NOT NULL DEFAULT 0,
    total_tokens        INT GENERATED ALWAYS AS (input_tokens + output_tokens) STORED,
    input_cost_usd      NUMERIC(10, 6) DEFAULT 0,
    output_cost_usd     NUMERIC(10, 6) DEFAULT 0,
    total_cost_usd      NUMERIC(10, 6) GENERATED ALWAYS AS
                         (input_cost_usd + output_cost_usd) STORED,

    -- Performance
    latency_ms          INT,
    is_primary           BOOLEAN DEFAULT FALSE,

    -- Feedback (future: thumbs up/down from field officer)
    rating              SMALLINT,     -- 1-5 or NULL
    rating_comment      TEXT,

    -- Audit
    created_at          TIMESTAMPTZ DEFAULT now(),
    service_type        VARCHAR(100),
    collection_slug     VARCHAR(255)
);

CREATE INDEX ix_llm_responses_appointment ON knowledge_schema.llm_responses(appointment_id);
CREATE INDEX ix_llm_responses_model ON knowledge_schema.llm_responses(model_id);
```

### 19.5 Token economics tracking

Every LLM call records:

| Field | Source | Used for |
|---|---|---|
| `input_tokens` | API response (usage.input_tokens) | Cost calc, optimization |
| `output_tokens` | API response (usage.output_tokens) | Cost calc, quota tracking |
| `input_cost_usd` | `input_tokens / 1000 * model.input_cost_per_1k` | Budget dashboards |
| `output_cost_usd` | `output_tokens / 1000 * model.output_cost_per_1k` | Budget dashboards |
| `latency_ms` | `time.time()` before/after call | Performance comparison |

**Token optimization strategies** (built into the pipeline):

1. **Prompt caching**: Claude supports prompt caching — if the system
   prompt + RAG context is reused across appointments with the same
   service type, cache it for 5 min. Saves ~90% of input tokens on
   cache hits.
2. **Context window fitting**: before sending, count tokens and trim
   RAG chunks from the bottom of the list if the total exceeds the
   model's `max_context_tokens`. Different models have different
   limits (GPT-4o: 128K, Llama 3: 8K, Gemini: 1M).
3. **Short-circuit for local models**: Ollama/Qwen run locally with
   zero API cost. Use them as the baseline; only fan out to paid
   models when the admin enables them.

### 19.6 Prometheus metrics

Emitted by knowledge_agent_svc on every LLM call:

```python
# Counters
llm_requests_total{model, provider, service_type, status}
llm_tokens_input_total{model, provider}
llm_tokens_output_total{model, provider}
llm_cost_usd_total{model, provider}

# Histograms
llm_latency_seconds{model, provider}
llm_tokens_per_request{model, provider, direction}  # input vs output

# Gauges
llm_models_enabled_count
rag_chunks_per_query{collection}
```

### 19.7 Grafana dashboards

Three dashboards, all fed by Prometheus:

**Dashboard 1: LLM Cost & Usage**
```
┌─────────────────────────────────────────────────────┐
│  Total cost today: $2.47                             │
│  Total tokens today: 142,000                         │
│                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │ Claude       │  │ GPT-4o      │  │ Ollama      │ │
│  │ $1.82        │  │ $0.65       │  │ $0.00       │ │
│  │ 85K tokens   │  │ 47K tokens  │  │ 10K tokens  │ │
│  └─────────────┘  └─────────────┘  └─────────────┘ │
│                                                     │
│  [time-series: cost per hour, stacked by model]      │
│  [time-series: tokens per hour, stacked by model]    │
└─────────────────────────────────────────────────────┘
```

**Dashboard 2: LLM Performance Comparison**
```
┌─────────────────────────────────────────────────────┐
│  Median latency by model (p50 / p95 / p99)           │
│  ┌──────────────────────────────────────────────┐    │
│  │ Ollama Llama3   │ 1.2s / 2.1s / 3.5s        │    │
│  │ GPT-4o-mini     │ 0.8s / 1.5s / 2.2s        │    │
│  │ Claude Sonnet   │ 1.5s / 2.8s / 4.0s        │    │
│  │ Gemini Flash    │ 0.5s / 0.9s / 1.3s        │    │
│  └──────────────────────────────────────────────┘    │
│                                                     │
│  [heatmap: latency distribution per model]           │
│  [bar chart: avg tokens per response by model]       │
└─────────────────────────────────────────────────────┘
```

**Dashboard 3: RAG Quality & Knowledge Base Health**
```
┌─────────────────────────────────────────────────────┐
│  Chunks indexed: 840   Active: 780   Expired: 60     │
│  Collections: 7   Repositories: 25                   │
│  Avg chunks per query: 5.2                           │
│  Avg similarity score: 0.82                          │
│                                                     │
│  [time-series: queries per hour]                     │
│  [bar chart: chunks by strategy (sentence/recursive/ │
│   semantic/parent_doc)]                              │
│  [table: most-queried collections]                   │
└─────────────────────────────────────────────────────┘
```

### 19.8 Kibana (ELK) logging

Structured JSON logs from knowledge_agent_svc, indexed by Kibana:

```json
{
  "timestamp": "2026-04-12T10:30:00Z",
  "event": "llm.response",
  "appointment_id": 42,
  "model_id": "claude-sonnet-4",
  "provider": "anthropic",
  "service_type": "Personal Care & Companionship",
  "input_tokens": 1200,
  "output_tokens": 350,
  "cost_usd": 0.0089,
  "latency_ms": 1850,
  "rag_chunks_used": 5,
  "rag_strategies": ["sentence", "recursive", "semantic"],
  "finish_reason": "end_turn",
  "is_primary": true
}
```

Enables: full-text search on response content, filtering by model,
drill-down from Grafana panels to individual requests, compliance
audit ("what did the LLM tell the field officer before this visit?").

### 19.9 Appointment detail — LLM Responses listing

Every portal (admin, support, field officer) shows a new
**Knowledge Briefings** section on the appointment detail page:

```
┌─────────────────────────────────────────────────────┐
│  Appointment #42 — claimed                           │
│  ...existing detail cards...                         │
│                                                     │
│  ── Knowledge Briefings ──────────────────────────   │
│                                                     │
│  ┌──────────────────────────────────────────────┐    │
│  │ ⭐ PRIMARY — Claude Sonnet 4                  │    │
│  │ 1,200 input / 350 output tokens   $0.009      │    │
│  │ Latency: 1.85s                                │    │
│  │                                               │    │
│  │ Based on 5 knowledge-base documents:           │    │
│  │ 1. Hygiene Guidelines — always wear gloves...  │    │
│  │ 2. Medication checklist — confirm schedule...  │    │
│  │ 3. Care protocol v4.2 — 5-step arrival...      │    │
│  │                                               │    │
│  │ [👍] [👎] [Expand full response]              │    │
│  └──────────────────────────────────────────────┘    │
│                                                     │
│  ┌──────────────────────────────────────────────┐    │
│  │ GPT-4o                                        │    │
│  │ 1,180 input / 280 output tokens   $0.006      │    │
│  │ Latency: 0.95s                                │    │
│  │                                               │    │
│  │ For this Personal Care visit, note the...      │    │
│  │                                               │    │
│  │ [👍] [👎] [Expand full response]              │    │
│  └──────────────────────────────────────────────┘    │
│                                                     │
│  ┌──────────────────────────────────────────────┐    │
│  │ Llama 3 (Ollama, local)                       │    │
│  │ 980 input / 420 output tokens   $0.000         │    │
│  │ Latency: 2.10s                                │    │
│  │                                               │    │
│  │ Before the visit, ensure you have reviewed...  │    │
│  │                                               │    │
│  │ [👍] [👎] [Expand full response]              │    │
│  └──────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

**Thumbs up/down** feeds back into the `rating` column on
`llm_responses` — future analytics can correlate rating with model,
service type, and prompt to improve over time.

### 19.10 Updated phase plan

| Phase | What | Status |
|---|---|---|
| **Phase 2c** | RAG search API | Next to build |
| **Phase 3a** | LLM model registry + llm_responses table + single-model briefing | Build after 2c |
| **Phase 3b** | Multi-LLM fan-out + token tracking + cost calculation | Build after 3a |
| **Phase 3c** | Slack threaded reply (primary model response) | Build after 3a |
| **Phase 3d** | Appointment detail Knowledge Briefings UI (all portals) | Build after 3b |
| **Phase 3e** | Thumbs up/down feedback loop | Build after 3d |
| **Phase 4** | Interactive Slack Q&A | After 3 |
| **Phase 5a** | Prometheus metrics for LLM calls | After 3b |
| **Phase 5b** | Grafana dashboards (cost, performance, RAG quality) | After 5a |
| **Phase 5c** | Kibana structured logging | After 5a |
| **Phase 5d** | Airflow + S3 + multi-tenant | After 5c |

---

### 19.11 Airflow fan-out + per-user model override

**Airflow as the LLM orchestrator** (not inline BackgroundTask):

When an appointment is claimed, the knowledge_agent_svc publishes a
Kafka event. **Airflow** (not the inline pipeline) picks it up and
fans out one task per enabled model — all run in parallel:

```
Kafka: appointment.claimed
    │
    ▼
Airflow DAG: llm_briefing_fanout
    │
    ├─► Task: rag_retrieve (shared — one query, reused by all models)
    │
    ├─► Task: call_claude     ──► store llm_response row
    ├─► Task: call_gpt4o      ──► store llm_response row
    ├─► Task: call_gemini     ──► store llm_response row
    ├─► Task: call_ollama     ──► store llm_response row
    ├─► Task: call_qwen       ──► store llm_response row
    │   (all parallel — Airflow fan-out)
    │
    ├─► Task: pick_primary
    │   Read the global config → determine which model is primary
    │   Mark that response row as is_primary=true
    │
    └─► Task: post_to_slack
        Post ONLY the primary response as a Slack threaded reply
```

**Why Airflow** (not BackgroundTask):
- Parallel execution across models (BackgroundTask is single-threaded)
- Per-task retries (if Claude is rate-limited, retry that task only)
- Monitoring UI (see which models succeeded/failed/are slow)
- DAG-level timeout (don't let a slow model block the others)

**Slack shows only one response:**

The Slack threaded reply always shows the **primary** model's
response. Which model is primary is determined by a cascade:

```
1. Per-appointment override (if the admin set a preferred model
   for this specific appointment) → use that model
2. Per-user preference (if the field officer set a preferred model
   in their profile) → use that model
3. Global default (system-level config: is_primary=true in the
   model registry) → use that model
```

**Data model for per-user override:**

```sql
-- In auth_schema.users (existing table)
ALTER TABLE auth_schema.users ADD COLUMN
    preferred_llm_model VARCHAR(50);  -- NULL = use global default

-- In appointment_schema.appointments (existing table)
ALTER TABLE appointment_schema.appointments ADD COLUMN
    preferred_llm_model VARCHAR(50);  -- NULL = use user pref → global
```

**Resolution logic** (in pick_primary task):

```python
def resolve_primary_model(appointment, user, model_registry):
    # 1. Appointment-level override
    if appointment.get('preferred_llm_model'):
        return appointment['preferred_llm_model']
    # 2. User-level preference
    if user.get('preferred_llm_model'):
        return user['preferred_llm_model']
    # 3. Global default
    for model in model_registry:
        if model.get('is_primary'):
            return model['id']
    # 4. Fallback
    return 'claude-sonnet-4'
```

**Admin portal: all responses visible**

Even though Slack shows only the primary, the **appointment detail
page** in admin/support/field portals shows ALL responses side by
side — every model's briefing, token count, cost, latency. This lets:

- **Admins** compare model quality and decide which to set as primary
- **Field officers** switch their preferred model if they find one
  produces better briefings for their service type
- **Auditors** see exactly what each model said about each appointment

**Per-user model preference in the UI:**

Field officers see a small dropdown on their **profile page** (or in
the appointment detail) letting them pick their preferred model. The
dropdown lists all enabled models with their display name and a cost
indicator ($, $$, $$$, or "free" for local models).

---

*This document is a living brainstorm. Mark decisions with ✅ as you
make them, then tell Claude "build phase N" to start implementation.*
