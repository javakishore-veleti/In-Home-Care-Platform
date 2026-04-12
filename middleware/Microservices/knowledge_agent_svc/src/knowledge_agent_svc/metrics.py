"""Prometheus metrics for LLM operations.

Exposed at /metrics on knowledge_agent_svc. Scraped by Prometheus,
visualized in Grafana dashboards.
"""
from prometheus_client import Counter, Histogram, Gauge, Info

# ----- LLM call metrics -----

LLM_REQUESTS = Counter(
    'llm_requests_total',
    'Total LLM API calls',
    ['model_id', 'provider', 'status'],
)

LLM_TOKENS_INPUT = Counter(
    'llm_tokens_input_total',
    'Total input tokens sent to LLMs',
    ['model_id', 'provider'],
)

LLM_TOKENS_OUTPUT = Counter(
    'llm_tokens_output_total',
    'Total output tokens received from LLMs',
    ['model_id', 'provider'],
)

LLM_COST_USD = Counter(
    'llm_cost_usd_total',
    'Total cost in USD across all LLM calls',
    ['model_id', 'provider'],
)

LLM_LATENCY = Histogram(
    'llm_latency_seconds',
    'LLM call latency in seconds',
    ['model_id', 'provider'],
    buckets=[0.5, 1, 2, 3, 5, 8, 10, 15, 30, 60],
)

LLM_RATINGS = Counter(
    'llm_ratings_total',
    'Star ratings given to LLM responses',
    ['model_id', 'rating'],
)

# ----- RAG metrics -----

RAG_QUERIES = Counter(
    'rag_queries_total',
    'Total RAG search queries',
    ['collection_slug'],
)

RAG_CHUNKS_PER_QUERY = Histogram(
    'rag_chunks_per_query',
    'Number of chunks returned per RAG query',
    ['collection_slug'],
    buckets=[0, 1, 2, 3, 5, 8, 10, 15, 20],
)

RAG_SIMILARITY_SCORE = Histogram(
    'rag_similarity_score',
    'Cosine similarity scores of retrieved chunks',
    ['collection_slug'],
    buckets=[0.3, 0.4, 0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1.0],
)

# ----- System gauges -----

LLM_MODELS_ENABLED = Gauge(
    'llm_models_enabled_count',
    'Number of currently enabled LLM models',
)

KNOWLEDGE_CHUNKS_ACTIVE = Gauge(
    'knowledge_chunks_active_total',
    'Total active chunks across all collections',
)

# ----- Briefing pipeline metrics -----

BRIEFINGS_TOTAL = Counter(
    'briefings_total',
    'Total briefing pipeline executions',
    ['service_type', 'status'],
)

BRIEFING_DURATION = Histogram(
    'briefing_duration_seconds',
    'Full briefing pipeline duration (RAG + all LLM calls + Slack post)',
    ['service_type'],
    buckets=[1, 2, 5, 10, 15, 30, 60],
)
