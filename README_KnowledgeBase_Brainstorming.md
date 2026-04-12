# Knowledge Base — Brainstorming Document

> **Status**: brainstorming / pre-implementation.
> Read, annotate, push back on anything, then tell Claude "build phase N" when ready.
>
> **Last updated**: 2026-04-11

---

## Table of Contents

- [1. The Insight](#1-the-insight)
- [2. Glean Parallel](#2-glean-parallel)
- [3. How It Maps to What We Already Have](#3-how-it-maps-to-what-we-already-have)
- [4. End-to-End User Story](#4-end-to-end-user-story)
- [5. Architecture Diagram](#5-architecture-diagram)
- [6. Existing Components That Plug In Directly](#6-existing-components-that-plug-in-directly)
- [7. Build Phases](#7-build-phases)
  - [Phase 1 — Collections + Items CRUD](#phase-1--collections--items-crud-2-days)
  - [Phase 2 — VectorDB Indexing + RAG Search](#phase-2--vectordb-indexing--rag-search-2-days)
  - [Phase 3 — LangGraph Briefing Agent + Slack Auto-Response](#phase-3--langgraph-briefing-agent--slack-auto-response-3-days)
  - [Phase 4 — Interactive Slack Q&A](#phase-4--interactive-slack-qa-2-days)
- [8. Key Technical Decisions](#8-key-technical-decisions)
- [9. Data Model (Draft)](#9-data-model-draft)
- [10. LangGraph Flow Design](#10-langgraph-flow-design)
- [11. Slack Threading UX](#11-slack-threading-ux)
- [12. What Makes This a Moat](#12-what-makes-this-a-moat)
- [13. Open Questions](#13-open-questions)

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

*This document is a living brainstorm. Mark decisions with ✅ as you
make them, then tell Claude "build phase N" to start implementation.*
