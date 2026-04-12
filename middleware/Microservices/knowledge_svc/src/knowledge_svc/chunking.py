"""Multi-strategy text chunking for RAG.

Four strategies produce chunks at different granularities from the
same source text. All are stored in the same collection_chunks table
with a `chunk_strategy` column. At retrieval time, pgvector's cosine
similarity naturally surfaces the best-granularity match regardless
of which strategy produced it.

Strategies
----------
sentence     — one chunk per sentence (5-30 words). Best for factual
               lookup queries.
recursive    — recursive split on \\n\\n → \\n → ". " → " " with
               target size ~300 chars and 50-char overlap. Best
               general-purpose. Respects paragraph boundaries.
semantic     — embed each sentence, merge adjacent sentences whose
               cosine similarity > threshold into one chunk. Follows
               topic boundaries. Requires an embedding function.
parent_doc   — the full item text as one chunk. Best for short items
               (announcements, notes) and as "parent context" when a
               smaller chunk matches.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any, Callable


def hash_chunk(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


# ----- Strategy: sentence -----

def chunk_sentence(text: str) -> list[str]:
    """Split on sentence boundaries. Keeps each sentence as one chunk."""
    if not text or not text.strip():
        return []
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 5]


# ----- Strategy: recursive -----

SEPARATORS = ['\n\n', '\n', '. ', ', ', ' ']


def chunk_recursive(
    text: str,
    chunk_size: int = 300,
    overlap: int = 50,
) -> list[str]:
    """Recursive character splitter that respects natural boundaries.

    Tries the most meaningful separator first (paragraph break), then
    falls through to less meaningful ones. Much better than a fixed
    character slicer because chunks land on paragraph/sentence
    boundaries instead of cutting mid-word.
    """
    if not text or not text.strip():
        return []
    text = text.strip()
    if len(text) <= chunk_size:
        return [text]

    return _split_recursive(text, SEPARATORS, chunk_size, overlap)


def _split_recursive(
    text: str,
    separators: list[str],
    chunk_size: int,
    overlap: int,
) -> list[str]:
    if not text.strip():
        return []
    if len(text) <= chunk_size:
        return [text.strip()]
    if not separators:
        # Fallback: hard split at chunk_size with overlap
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

    sep = separators[0]
    rest = separators[1:]
    parts = text.split(sep)

    chunks = []
    current = ''
    for part in parts:
        candidate = (current + sep + part).strip() if current else part.strip()
        if len(candidate) <= chunk_size:
            current = candidate
        else:
            if current.strip():
                chunks.append(current.strip())
            if len(part.strip()) > chunk_size:
                # This part is itself too big — recurse with next separator
                chunks.extend(_split_recursive(part.strip(), rest, chunk_size, overlap))
                current = ''
            else:
                current = part.strip()
    if current.strip():
        chunks.append(current.strip())

    return [c for c in chunks if c]


# ----- Strategy: semantic -----

def chunk_semantic(
    text: str,
    embed_fn: Callable[[list[str]], list[list[float]]],
    similarity_threshold: float = 0.75,
) -> list[str]:
    """Group adjacent sentences by embedding similarity.

    Sentences whose embeddings are within ``similarity_threshold``
    cosine distance of each other get merged into one chunk. The
    result follows topic boundaries rather than character counts.
    """
    sentences = chunk_sentence(text)
    if len(sentences) <= 1:
        return sentences

    embeddings = embed_fn(sentences)

    chunks: list[str] = []
    current_group = [sentences[0]]
    current_emb = embeddings[0]

    for i in range(1, len(sentences)):
        sim = _cosine_similarity(current_emb, embeddings[i])
        if sim >= similarity_threshold:
            current_group.append(sentences[i])
            # Update the group embedding to the average
            current_emb = _avg_vectors(current_emb, embeddings[i])
        else:
            chunks.append(' '.join(current_group))
            current_group = [sentences[i]]
            current_emb = embeddings[i]

    if current_group:
        chunks.append(' '.join(current_group))

    return [c for c in chunks if c.strip()]


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _avg_vectors(a: list[float], b: list[float]) -> list[float]:
    return [(x + y) / 2.0 for x, y in zip(a, b)]


# ----- Strategy: parent_doc -----

def chunk_parent_doc(text: str) -> list[str]:
    """The full text as one chunk. One per item."""
    if not text or not text.strip():
        return []
    return [text.strip()]


# ----- Run all strategies -----

STRATEGIES = {
    'sentence': chunk_sentence,
    'recursive': chunk_recursive,
    'parent_doc': chunk_parent_doc,
    # 'semantic' is handled separately because it needs an embed_fn
}


def run_all_strategies(
    text: str,
    embed_fn: Callable[[list[str]], list[list[float]]] | None = None,
) -> list[dict[str, Any]]:
    """Run all chunking strategies on the same text.

    Returns a list of dicts with keys: chunk_text, chunk_strategy,
    chunk_index, content_hash, token_count.
    """
    results: list[dict[str, Any]] = []

    for strategy_name, chunk_fn in STRATEGIES.items():
        chunks = chunk_fn(text)
        for idx, chunk in enumerate(chunks):
            results.append({
                'chunk_text': chunk,
                'chunk_strategy': strategy_name,
                'chunk_index': idx,
                'content_hash': hash_chunk(f'{strategy_name}:{chunk}'),
                'token_count': len(chunk.split()),
            })

    # Semantic requires embed_fn
    if embed_fn is not None:
        try:
            semantic_chunks = chunk_semantic(text, embed_fn)
            for idx, chunk in enumerate(semantic_chunks):
                results.append({
                    'chunk_text': chunk,
                    'chunk_strategy': 'semantic',
                    'chunk_index': idx,
                    'content_hash': hash_chunk(f'semantic:{chunk}'),
                    'token_count': len(chunk.split()),
                })
        except Exception:
            # Semantic chunking is best-effort — if embedding fails,
            # the other 3 strategies still produce usable chunks.
            pass

    return results
