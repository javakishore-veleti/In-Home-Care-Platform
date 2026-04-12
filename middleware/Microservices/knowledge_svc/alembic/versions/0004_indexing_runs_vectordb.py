"""add vectordb_engine to indexing_runs

Revision ID: 0004
Revises: 0003
Create Date: 2026-04-11

Each indexing run targets a specific vector DB engine. The admin selects
which engines to index into via checkboxes on the repository detail page.
Publishing creates one indexing_run row per selected engine so the history
shows exactly what was indexed where and when.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0004'
down_revision: Union[str, None] = '0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = {c['name'] for c in inspector.get_columns('indexing_runs', schema='knowledge_schema')}
    if 'vectordb_engine' not in existing:
        op.add_column(
            'indexing_runs',
            sa.Column('vectordb_engine', sa.String(30), server_default='pgvector'),
            schema='knowledge_schema',
        )
        op.create_index(
            'ix_indexing_runs_vectordb',
            'indexing_runs',
            ['repository_id', 'vectordb_engine'],
            schema='knowledge_schema',
        )


def downgrade() -> None:
    op.execute('DROP INDEX IF EXISTS knowledge_schema.ix_indexing_runs_vectordb')
    op.execute('ALTER TABLE knowledge_schema.indexing_runs DROP COLUMN IF EXISTS vectordb_engine')
