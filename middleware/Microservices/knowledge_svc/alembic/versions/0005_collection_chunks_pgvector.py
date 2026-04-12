"""enable pgvector + create collection_chunks table

Revision ID: 0005
Revises: 0004
Create Date: 2026-04-11

Enables the pgvector extension in the same Postgres instance and
creates the collection_chunks table with a VECTOR(384) column for
sentence-transformers all-MiniLM-L6-v2 embeddings (384 dimensions).
If you switch to OpenAI text-embedding-3-small later, change to
VECTOR(1536) and re-index.

LiveVectorLake-inspired: content_hash for dedup, valid_from/valid_until
for temporal queries.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0005'
down_revision: Union[str, None] = '0004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBEDDING_DIM = 384


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table('collection_chunks', schema='knowledge_schema'):
        return

    op.execute(f'''
        CREATE TABLE knowledge_schema.collection_chunks (
            id              SERIAL PRIMARY KEY,
            item_id         INT NOT NULL REFERENCES knowledge_schema.repository_items(id) ON DELETE CASCADE,
            repository_id   INT NOT NULL REFERENCES knowledge_schema.repositories(id) ON DELETE CASCADE,
            collection_id   INT NOT NULL REFERENCES knowledge_schema.collections(id),
            chunk_index     INT NOT NULL,
            chunk_text      TEXT NOT NULL,
            embedding       vector({EMBEDDING_DIM}),
            content_hash    CHAR(64) NOT NULL,
            token_count     INT,
            valid_from      TIMESTAMPTZ NOT NULL DEFAULT now(),
            valid_until     TIMESTAMPTZ,
            created_at      TIMESTAMPTZ DEFAULT now()
        )
    ''')

    op.create_index(
        'ix_chunks_collection_active',
        'collection_chunks',
        ['collection_id'],
        schema='knowledge_schema',
        postgresql_where=sa.text('valid_until IS NULL'),
    )
    op.create_index(
        'ix_chunks_content_hash',
        'collection_chunks',
        ['content_hash'],
        schema='knowledge_schema',
    )
    op.create_index(
        'ix_chunks_repository',
        'collection_chunks',
        ['repository_id'],
        schema='knowledge_schema',
    )


def downgrade() -> None:
    op.execute('DROP TABLE IF EXISTS knowledge_schema.collection_chunks')
