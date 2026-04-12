"""Inline indexing pipeline — chunks text, embeds, stores in pgvector.

Called by the Publish/Reindex route via BackgroundTasks. Each call
processes one repository for one vector DB engine. The pipeline:

  1. Gather all item texts for the repository.
  2. Chunk each text (recursive character splitter).
  3. Hash each chunk (SHA-256 for LiveVectorLake-style dedup).
  4. Skip chunks whose hash already exists + is still active.
  5. Embed new chunks via sentence-transformers (local, free).
  6. INSERT into knowledge_schema.collection_chunks.
  7. Soft-delete chunks that no longer appear (valid_until = now).

Uses sentence-transformers all-MiniLM-L6-v2 by default (384 dim,
runs on CPU, no API key). Set EMBEDDING_PROVIDER=openai +
OPENAI_API_KEY for production quality (1536 dim — also needs the
migration dimension updated).
"""
from __future__ import annotations

import hashlib
import logging
import os
import time
from typing import Any

log = logging.getLogger(__name__)

EMBEDDING_PROVIDER = os.getenv('EMBEDDING_PROVIDER', 'sentence-transformers')
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', '400'))
CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', '50'))

_st_model = None


def _get_st_model():
    global _st_model
    if _st_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _st_model = SentenceTransformer(EMBEDDING_MODEL)
            log.info('indexing.model_loaded model=%s', EMBEDDING_MODEL)
        except ImportError:
            log.error('indexing.sentence_transformers_not_installed — pip install sentence-transformers')
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


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Simple recursive character splitter."""
    if not text or not text.strip():
        return []
    text = text.strip()
    if len(text) <= chunk_size:
        return [text]
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - overlap
        if start >= len(text):
            break
    return chunks


def hash_chunk(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def run_indexing_pipeline(
    *,
    repository_id: int,
    collection_id: int,
    vectordb_engine: str,
    run_id: int,
) -> dict[str, int]:
    """Execute the full pipeline for one repo + one engine.

    Returns {chunks_indexed, chunks_skipped, chunks_expired}.
    Raises on fatal errors (caller catches and marks the run failed).
    """
    from shared.storage import get_database_url, now_utc

    if vectordb_engine != 'pgvector':
        log.info('indexing.engine_not_implemented engine=%s — skipping', vectordb_engine)
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
        with conn.cursor() as cur:
            # 1. Gather all item texts
            cur.execute(
                '''
                SELECT id, title, content_text, item_type
                FROM knowledge_schema.repository_items
                WHERE repository_id = %s
                ''',
                (repository_id,),
            )
            items = cur.fetchall()

        texts_to_process: list[dict[str, Any]] = []
        for item in items:
            raw = item.get('content_text') or ''
            if not raw.strip():
                raw = item.get('title', '')
            chunks = chunk_text(raw)
            for idx, chunk in enumerate(chunks):
                texts_to_process.append({
                    'item_id': item['id'],
                    'chunk_index': idx,
                    'chunk_text': chunk,
                    'content_hash': hash_chunk(chunk),
                    'token_count': len(chunk.split()),
                })

        if not texts_to_process:
            log.info('indexing.no_text repository_id=%d', repository_id)
            return {'chunks_indexed': 0, 'chunks_skipped': 0, 'chunks_expired': 0}

        # 2. Check existing hashes for dedup
        with conn.cursor() as cur:
            cur.execute(
                '''
                SELECT content_hash FROM knowledge_schema.collection_chunks
                WHERE repository_id = %s AND valid_until IS NULL
                ''',
                (repository_id,),
            )
            existing_hashes = {row['content_hash'] for row in cur.fetchall()}

        new_chunks = [c for c in texts_to_process if c['content_hash'] not in existing_hashes]
        skipped = len(texts_to_process) - len(new_chunks)

        # 3. Embed new chunks
        if new_chunks:
            chunk_texts = [c['chunk_text'] for c in new_chunks]
            log.info('indexing.embedding count=%d model=%s', len(chunk_texts), EMBEDDING_MODEL)
            embeddings = embed_texts(chunk_texts)

            # 4. INSERT into pgvector
            now = now_utc()
            with conn.cursor() as cur:
                for chunk_data, emb in zip(new_chunks, embeddings):
                    cur.execute(
                        '''
                        INSERT INTO knowledge_schema.collection_chunks
                            (item_id, repository_id, collection_id, chunk_index,
                             chunk_text, embedding, content_hash, token_count, valid_from)
                        VALUES (%s, %s, %s, %s, %s, %s::vector, %s, %s, %s)
                        ON CONFLICT DO NOTHING
                        ''',
                        (
                            chunk_data['item_id'],
                            repository_id,
                            collection_id,
                            chunk_data['chunk_index'],
                            chunk_data['chunk_text'],
                            str(emb),
                            chunk_data['content_hash'],
                            chunk_data['token_count'],
                            now,
                        ),
                    )

        # 5. Soft-delete chunks that disappeared (old content removed)
        new_hashes = {c['content_hash'] for c in texts_to_process}
        expired_hashes = existing_hashes - new_hashes
        expired_count = 0
        if expired_hashes:
            with conn.cursor() as cur:
                for h in expired_hashes:
                    cur.execute(
                        '''
                        UPDATE knowledge_schema.collection_chunks
                        SET valid_until = now()
                        WHERE repository_id = %s AND content_hash = %s AND valid_until IS NULL
                        ''',
                        (repository_id, h),
                    )
                    expired_count += cur.rowcount

        # 6. Update chunk_count on the repository
        with conn.cursor() as cur:
            cur.execute(
                '''
                UPDATE knowledge_schema.repositories SET
                    chunk_count = (
                        SELECT COUNT(*) FROM knowledge_schema.collection_chunks
                        WHERE repository_id = %s AND valid_until IS NULL
                    ),
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
