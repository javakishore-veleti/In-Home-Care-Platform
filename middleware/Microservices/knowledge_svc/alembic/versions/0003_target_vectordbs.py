"""add target_vectordbs column to repositories

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-11

Each repository can be indexed into one or more vector databases.
The admin selects targets via checkboxes on the repository detail page.
Default: pgvector only (zero extra infra — same Postgres).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0003'
down_revision: Union[str, None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = {c['name'] for c in inspector.get_columns('repositories', schema='knowledge_schema')}
    if 'target_vectordbs' not in existing:
        op.add_column(
            'repositories',
            sa.Column('target_vectordbs', sa.ARRAY(sa.Text), server_default='{pgvector}'),
            schema='knowledge_schema',
        )


def downgrade() -> None:
    op.execute('ALTER TABLE knowledge_schema.repositories DROP COLUMN IF EXISTS target_vectordbs')
