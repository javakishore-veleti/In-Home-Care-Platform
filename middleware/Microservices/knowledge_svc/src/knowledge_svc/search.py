"""RAG search — multi-strategy retrieval with de-duplication.

Given a natural-language query and a collection, this module:
  1. Masks known service-type names in the query (EICopilot pattern)
     so similarity matches on *intent*, not surface entity overlap.
  2. Embeds the masked query via sentence-transformers.
  3. Queries pgvector across ALL chunk strategies in one cosine-sim
     call — the vector index naturally surfaces the best-granularity
     match.
  4. De-duplicates overlapping chunks from the same item (if a
     sentence chunk is a substring of a recursive chunk, keep only
     the larger one).
  5. Returns top-K chunks with source metadata, ready to paste into
     an LLM prompt.
"""
from __future__ import annotations

import logging
import os
import re
from typing import Any

log = logging.getLogger(__name__)

SERVICE_TYPE_NAMES: list[str] | None = None


def _get_service_type_names() -> list[str]:
    """Lazy-load known service type names for query masking."""
    global SERVICE_TYPE_NAMES
    if SERVICE_TYPE_NAMES is not None:
        return SERVICE_TYPE_NAMES
    try:
        from .store import CollectionStore
        store = CollectionStore()
        collections = store.list_collections()
        SERVICE_TYPE_NAMES = sorted(
            [c.get('name', '') for c in collections if c.get('name')],
            key=len,
            reverse=True,
        )
    except Exception:
        SERVICE_TYPE_NAMES = []
    return SERVICE_TYPE_NAMES


def mask_service_types(query: str) -> str:
    """Replace known service-type names with <SERVICE_TYPE> so the
    embedding matches on intent structure, not entity overlap.

    EICopilot paper (arxiv 2501.13746): this improved retrieval
    accuracy from 17-41% to 82-84%.
    """
    masked = query
    for name in _get_service_type_names():
        if name.lower() in masked.lower():
            pattern = re.compile(re.escape(name), re.IGNORECASE)
            masked = pattern.sub('<SERVICE_TYPE>', masked)
    return masked


def deduplicate_by_containment(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """If chunk A is a substring of chunk B from the same item, drop A."""
    if not results:
        return results
    kept: list[dict[str, Any]] = []
    for r in results:
        is_contained = False
        r_text = r.get('chunk_text', '')
        r_item = r.get('item_id')
        for other in results:
            if other is r:
                continue
            if (other.get('item_id') == r_item
                    and r_text in other.get('chunk_text', '')
                    and len(other.get('chunk_text', '')) > len(r_text)):
                is_contained = True
                break
        if not is_contained:
            kept.append(r)
    return kept


def search(
    *,
    collection_id: int | None = None,
    collection_slug: str | None = None,
    query: str,
    top_k: int = 10,
    strategy_filter: str | None = None,
) -> list[dict[str, Any]]:
    """Execute a RAG search against pgvector.

    Returns up to ``top_k`` de-duplicated chunks ranked by cosine
    similarity, with source metadata.
    """
    from .indexing import embed_texts
    from shared.storage import BaseStore

    store = BaseStore('_')
    if not store.using_db:
        log.warning('search.no_db — pgvector search requires Postgres')
        return []

    # Resolve collection_id from slug if needed
    if collection_id is None and collection_slug:
        from .store import CollectionStore
        cstore = CollectionStore()
        col = cstore.get_collection_by_slug(collection_slug)
        if not col:
            return []
        collection_id = col['id']

    # 1. Mask service-type names (EICopilot)
    masked_query = mask_service_types(query)
    log.info('search.query original="%s" masked="%s" collection_id=%s', query, masked_query, collection_id)

    # 2. Embed the masked query
    embeddings = embed_texts([masked_query])
    if not embeddings:
        return []
    query_embedding = embeddings[0]

    # 3. Query pgvector — all strategies in one call
    where_clauses = ['c.valid_until IS NULL']
    params: list[Any] = []

    if collection_id is not None:
        where_clauses.append('c.collection_id = %s')
        params.append(collection_id)

    if strategy_filter:
        where_clauses.append('c.chunk_strategy = %s')
        params.append(strategy_filter)

    where_sql = ' AND '.join(where_clauses)
    emb_str = str(query_embedding)

    # Fetch more than top_k so dedup has room to remove overlaps
    fetch_limit = top_k * 3

    raw_results = store.fetch_all(
        f'''
        SELECT c.id, c.item_id, c.chunk_index, c.chunk_text,
               c.chunk_strategy,
               c.embedding <=> '{emb_str}'::vector AS similarity_score,
               LEFT(c.content_hash, 12) AS content_hash_short,
               c.token_count, c.repository_id, c.collection_id,
               i.title AS item_title, i.item_type,
               r.name AS repository_name,
               col.name AS collection_name, col.slug AS collection_slug
        FROM knowledge_schema.collection_chunks c
        LEFT JOIN knowledge_schema.repository_items i ON i.id = c.item_id
        LEFT JOIN knowledge_schema.repositories r ON r.id = c.repository_id
        LEFT JOIN knowledge_schema.collections col ON col.id = c.collection_id
        WHERE {where_sql}
        ORDER BY c.embedding <=> '{emb_str}'::vector ASC
        LIMIT {fetch_limit}
        ''',
        tuple(params),
    )

    log.info('search.raw_results count=%d', len(raw_results))

    # 4. De-duplicate overlapping chunks
    deduped = deduplicate_by_containment(raw_results)

    # 5. Return top_k
    results = deduped[:top_k]

    # Convert similarity_score (distance) to a 0-1 relevance score
    for r in results:
        dist = float(r.get('similarity_score', 1.0))
        r['relevance_score'] = round(max(0.0, 1.0 - dist), 4)

    log.info('search.results count=%d (after dedup from %d raw)', len(results), len(raw_results))
    return results
