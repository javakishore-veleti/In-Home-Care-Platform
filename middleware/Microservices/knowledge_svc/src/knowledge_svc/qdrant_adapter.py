"""Qdrant vector DB adapter for the indexing pipeline.

Writes chunks + embeddings to a Qdrant collection alongside (or instead
of) pgvector. Uses the Qdrant REST API directly — no qdrant-client
dependency needed.

Config via env:
  QDRANT_URL  default: http://localhost:6333
"""
from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from typing import Any

log = logging.getLogger(__name__)

QDRANT_URL = os.getenv('QDRANT_URL', 'http://localhost:6333')
EMBEDDING_DIM = 384


def _qdrant_call(method: str, path: str, payload: dict | None = None) -> dict[str, Any] | None:
    url = f'{QDRANT_URL}{path}'
    headers = {'Content-Type': 'application/json'}
    data = json.dumps(payload).encode('utf-8') if payload else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode('utf-8', 'ignore')[:500]
        log.warning('qdrant.http_error path=%s status=%d body=%s', path, exc.code, body)
        return None
    except (urllib.error.URLError, TimeoutError) as exc:
        log.warning('qdrant.network_error path=%s error=%s', path, exc)
        return None


def ensure_collection(collection_name: str) -> bool:
    """Create the Qdrant collection if it doesn't exist."""
    result = _qdrant_call('GET', f'/collections/{collection_name}')
    if result and result.get('status') == 'ok':
        return True
    create_result = _qdrant_call('PUT', f'/collections/{collection_name}', {
        'vectors': {'size': EMBEDDING_DIM, 'distance': 'Cosine'},
    })
    if create_result and create_result.get('status') == 'ok':
        log.info('qdrant.collection_created name=%s', collection_name)
        return True
    return False


def upsert_chunks(
    collection_name: str,
    chunks: list[dict[str, Any]],
    embeddings: list[list[float]],
) -> int:
    """Upsert chunk vectors + payloads into a Qdrant collection.

    Returns the number of points upserted.
    """
    if not ensure_collection(collection_name):
        log.error('qdrant.collection_unavailable name=%s', collection_name)
        return 0

    points = []
    for chunk, emb in zip(chunks, embeddings):
        points.append({
            'id': hash(chunk.get('content_hash', '')) & 0x7FFFFFFFFFFFFFFF,
            'vector': emb,
            'payload': {
                'chunk_text': chunk.get('chunk_text', ''),
                'chunk_strategy': chunk.get('chunk_strategy', ''),
                'chunk_index': chunk.get('chunk_index', 0),
                'item_id': chunk.get('item_id', 0),
                'content_hash': chunk.get('content_hash', ''),
                'token_count': chunk.get('token_count', 0),
            },
        })

    result = _qdrant_call('PUT', f'/collections/{collection_name}/points', {'points': points})
    if result and result.get('status') == 'ok':
        log.info('qdrant.upserted collection=%s count=%d', collection_name, len(points))
        return len(points)
    return 0


def search(
    collection_name: str,
    query_embedding: list[float],
    top_k: int = 10,
) -> list[dict[str, Any]]:
    """Search a Qdrant collection by cosine similarity."""
    result = _qdrant_call('POST', f'/collections/{collection_name}/points/search', {
        'vector': query_embedding,
        'limit': top_k,
        'with_payload': True,
    })
    if not result or result.get('status') != 'ok':
        return []
    return [
        {**hit.get('payload', {}), 'score': hit.get('score', 0)}
        for hit in result.get('result', [])
    ]
