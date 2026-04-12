"""Inline indexing pipeline — multi-strategy chunking + embedding + pgvector.

Called by the Publish/Reindex route via BackgroundTasks. Each call
processes one repository for one vector DB engine. The pipeline:

  1. Gather all item texts for the repository.
  2. Run all 4 chunking strategies on each item (sentence, recursive,
     semantic, parent_doc) via the chunking module.
  3. Hash each chunk (SHA-256 with strategy prefix for dedup).
  4. Skip chunks whose hash already exists + is still active.
  5. Embed new chunks via sentence-transformers (local, free).
  6. INSERT into knowledge_schema.collection_chunks with chunk_strategy.
  7. Soft-delete chunks that no longer appear (valid_until = now).
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any

log = logging.getLogger(__name__)

EMBEDDING_PROVIDER = os.getenv('EMBEDDING_PROVIDER', 'sentence-transformers')
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')

_st_model = None


def _get_st_model():
    global _st_model
    if _st_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _st_model = SentenceTransformer(EMBEDDING_MODEL)
            log.info('indexing.model_loaded model=%s', EMBEDDING_MODEL)
        except ImportError:
            log.error('indexing.sentence_transformers_not_installed')
            raise
    return _st_model


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    if EMBEDDING_PROVIDER == 'sentence-transformers':
        model = _get_st_model()
        embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
        return [emb.tolist() for emb in embeddings]
    raise ValueError(f'Unknown EMBEDDING_PROVIDER: {EMBEDDING_PROVIDER}')


def run_indexing_pipeline(
    *,
    repository_id: int,
    collection_id: int,
    vectordb_engine: str,
    run_id: int,
) -> dict[str, Any]:
    """Execute the full multi-strategy pipeline for one repo + one engine."""
    from shared.storage import get_database_url, now_utc
    from .chunking import run_all_strategies

    if vectordb_engine == 'qdrant':
        return _run_qdrant_pipeline(repository_id, collection_id)

    if vectordb_engine != 'pgvector':
        log.info('indexing.engine_not_implemented engine=%s', vectordb_engine)
        return {'chunks_indexed': 0, 'chunks_skipped': 0, 'chunks_expired': 0}

    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError:
        log.error('indexing.psycopg_not_installed')
        raise

    db_url = get_database_url()
    t0 = time.time()

    with psycopg.connect(db_url, row_factory=dict_row) as conn:
        # 1. Gather all item texts
        with conn.cursor() as cur:
            cur.execute(
                'SELECT id, title, content_text, item_type FROM knowledge_schema.repository_items WHERE repository_id = %s',
                (repository_id,),
            )
            items = cur.fetchall()

        # 2. Run all 4 strategies on each item
        all_chunks: list[dict[str, Any]] = []
        for item in items:
            raw = item.get('content_text') or ''
            if not raw.strip():
                raw = item.get('title', '')
            if not raw.strip():
                continue
            item_chunks = run_all_strategies(raw, embed_fn=embed_texts)
            for chunk in item_chunks:
                chunk['item_id'] = item['id']
            all_chunks.extend(item_chunks)

        if not all_chunks:
            log.info('indexing.no_text repository_id=%d', repository_id)
            return {'chunks_indexed': 0, 'chunks_skipped': 0, 'chunks_expired': 0}

        # 3. Check existing hashes for dedup
        with conn.cursor() as cur:
            cur.execute(
                'SELECT content_hash FROM knowledge_schema.collection_chunks WHERE repository_id = %s AND valid_until IS NULL',
                (repository_id,),
            )
            existing_hashes = {row['content_hash'] for row in cur.fetchall()}

        new_chunks = [c for c in all_chunks if c['content_hash'] not in existing_hashes]
        skipped = len(all_chunks) - len(new_chunks)

        # 4. Embed new chunks
        if new_chunks:
            chunk_texts = [c['chunk_text'] for c in new_chunks]
            log.info('indexing.embedding count=%d strategies=%s model=%s',
                     len(chunk_texts),
                     sorted(set(c['chunk_strategy'] for c in new_chunks)),
                     EMBEDDING_MODEL)
            embeddings = embed_texts(chunk_texts)

            # 5. INSERT into pgvector
            now = now_utc()
            with conn.cursor() as cur:
                for chunk_data, emb in zip(new_chunks, embeddings):
                    cur.execute(
                        '''
                        INSERT INTO knowledge_schema.collection_chunks
                            (item_id, repository_id, collection_id, chunk_index,
                             chunk_text, chunk_strategy, embedding, content_hash,
                             token_count, valid_from)
                        VALUES (%s, %s, %s, %s, %s, %s, %s::vector, %s, %s, %s)
                        ON CONFLICT DO NOTHING
                        ''',
                        (
                            chunk_data['item_id'],
                            repository_id,
                            collection_id,
                            chunk_data['chunk_index'],
                            chunk_data['chunk_text'],
                            chunk_data['chunk_strategy'],
                            str(emb),
                            chunk_data['content_hash'],
                            chunk_data['token_count'],
                            now,
                        ),
                    )

        # 6. Soft-delete chunks that disappeared
        new_hashes = {c['content_hash'] for c in all_chunks}
        expired_hashes = existing_hashes - new_hashes
        expired_count = 0
        if expired_hashes:
            with conn.cursor() as cur:
                for h in expired_hashes:
                    cur.execute(
                        'UPDATE knowledge_schema.collection_chunks SET valid_until = now() WHERE repository_id = %s AND content_hash = %s AND valid_until IS NULL',
                        (repository_id, h),
                    )
                    expired_count += cur.rowcount

        # 7. Update chunk_count on the repository
        with conn.cursor() as cur:
            cur.execute(
                '''
                UPDATE knowledge_schema.repositories SET
                    chunk_count = (SELECT COUNT(*) FROM knowledge_schema.collection_chunks WHERE repository_id = %s AND valid_until IS NULL),
                    updated_at = now()
                WHERE id = %s
                ''',
                (repository_id, repository_id),
            )

    elapsed = time.time() - t0
    log.info(
        'indexing.done repository_id=%d engine=%s indexed=%d skipped=%d expired=%d elapsed=%.1fs',
        repository_id, vectordb_engine, len(new_chunks), skipped, expired_count, elapsed,
    )
    return {
        'chunks_indexed': len(new_chunks),
        'chunks_skipped': skipped,
        'chunks_expired': expired_count,
        'duration_seconds': round(elapsed, 2),
    }


def _run_qdrant_pipeline(repository_id: int, collection_id: int) -> dict[str, Any]:
    """Qdrant indexing: chunk + embed + upsert into Qdrant collection."""
    from shared.storage import BaseStore
    from .chunking import run_all_strategies
    from .qdrant_adapter import upsert_chunks

    t0 = time.time()
    store = BaseStore('_')
    if not store.using_db:
        return {'chunks_indexed': 0, 'chunks_skipped': 0, 'chunks_expired': 0}

    items = store.fetch_all(
        'SELECT id, title, content_text, item_type FROM knowledge_schema.repository_items WHERE repository_id = %s',
        (repository_id,),
    )

    all_chunks: list[dict[str, Any]] = []
    for item in items:
        raw = item.get('content_text') or item.get('title', '')
        if not raw.strip():
            continue
        item_chunks = run_all_strategies(raw, embed_fn=embed_texts)
        for chunk in item_chunks:
            chunk['item_id'] = item['id']
        all_chunks.extend(item_chunks)

    if not all_chunks:
        return {'chunks_indexed': 0, 'chunks_skipped': 0, 'chunks_expired': 0}

    chunk_texts = [c['chunk_text'] for c in all_chunks]
    embeddings = embed_texts(chunk_texts)

    collection_name = f'collection_{collection_id}'
    count = upsert_chunks(collection_name, all_chunks, embeddings)

    elapsed = time.time() - t0
    log.info('indexing.qdrant_done repository_id=%d indexed=%d elapsed=%.1fs', repository_id, count, elapsed)
    return {'chunks_indexed': count, 'chunks_skipped': 0, 'chunks_expired': 0, 'duration_seconds': round(elapsed, 2)}
