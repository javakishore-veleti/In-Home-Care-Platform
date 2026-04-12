"""add chunk_strategy column to collection_chunks

Revision ID: 0006
Revises: 0005
Create Date: 2026-04-12

Each chunk is produced by one of four strategies (sentence, recursive,
semantic, parent_doc). The same item text generates multiple chunk sets
stored in the same table, differentiated by this column. The pgvector
cosine-similarity index covers all strategies — no separate indexes.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0006'
down_revision: Union[str, None] = '0005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = {c['name'] for c in inspector.get_columns('collection_chunks', schema='knowledge_schema')}
    if 'chunk_strategy' not in existing:
        op.add_column(
            'collection_chunks',
            sa.Column('chunk_strategy', sa.String(30), nullable=False, server_default='recursive'),
            schema='knowledge_schema',
        )
        op.create_index(
            'ix_chunks_strategy',
            'collection_chunks',
            ['chunk_strategy'],
            schema='knowledge_schema',
        )


def downgrade() -> None:
    op.execute('DROP INDEX IF EXISTS knowledge_schema.ix_chunks_strategy')
    op.execute('ALTER TABLE knowledge_schema.collection_chunks DROP COLUMN IF EXISTS chunk_strategy')
