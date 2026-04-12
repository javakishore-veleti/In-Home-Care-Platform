"""create knowledge base tables

Revision ID: 0001
Revises: None
Create Date: 2026-04-11

Creates the full knowledge-base schema: collections, repositories,
repository_items, and indexing_runs. collection_chunks (with vector
embeddings) is added in a later migration when VectorDB indexing is
wired up (Phase 2b).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE SCHEMA IF NOT EXISTS knowledge_schema')

    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table('collections', schema='knowledge_schema'):
        op.create_table(
            'collections',
            sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('slug', sa.String(255), nullable=False, unique=True),
            sa.Column('service_type', sa.String(100)),
            sa.Column('description', sa.Text),
            sa.Column('icon_emoji', sa.String(10), server_default="'📚'"),
            sa.Column('org_id', sa.String(100), nullable=False, server_default='platform'),
            sa.Column('jurisdiction', sa.String(20)),
            sa.Column('repo_count', sa.Integer, server_default='0'),
            sa.Column('total_chunks', sa.Integer, server_default='0'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            schema='knowledge_schema',
        )

    if not inspector.has_table('repositories', schema='knowledge_schema'):
        op.create_table(
            'repositories',
            sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
            sa.Column('collection_id', sa.Integer, nullable=False),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('slug', sa.String(255), nullable=False),
            sa.Column('repo_type', sa.String(30), nullable=False, server_default='others'),
            sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
            sa.Column('description', sa.Text),
            sa.Column('source_mode', sa.String(10), server_default='local'),
            sa.Column('source_path', sa.String(1024)),
            sa.Column('org_id', sa.String(100), nullable=False, server_default='platform'),
            sa.Column('jurisdictions', sa.ARRAY(sa.Text)),
            sa.Column('item_count', sa.Integer, server_default='0'),
            sa.Column('chunk_count', sa.Integer, server_default='0'),
            sa.Column('last_indexed_at', sa.DateTime(timezone=True)),
            sa.Column('last_error', sa.Text),
            sa.Column('created_by_user_id', sa.Integer),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.ForeignKeyConstraint(['collection_id'], ['knowledge_schema.collections.id'], ondelete='CASCADE'),
            sa.UniqueConstraint('collection_id', 'slug', name='uq_repo_collection_slug'),
            schema='knowledge_schema',
        )
        op.create_index('ix_repositories_collection_id', 'repositories', ['collection_id'], schema='knowledge_schema')
        op.create_index('ix_repositories_status', 'repositories', ['status'], schema='knowledge_schema')

    if not inspector.has_table('repository_items', schema='knowledge_schema'):
        op.create_table(
            'repository_items',
            sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
            sa.Column('repository_id', sa.Integer, nullable=False),
            sa.Column('collection_id', sa.Integer, nullable=False),
            sa.Column('item_type', sa.String(20), nullable=False),
            sa.Column('title', sa.String(255), nullable=False),
            sa.Column('content_text', sa.Text),
            sa.Column('source_url', sa.String(2048)),
            sa.Column('file_path', sa.String(512)),
            sa.Column('file_name', sa.String(255)),
            sa.Column('file_size_bytes', sa.BigInteger),
            sa.Column('mime_type', sa.String(100)),
            sa.Column('chunk_count', sa.Integer, server_default='0'),
            sa.Column('org_id', sa.String(100), nullable=False, server_default='platform'),
            sa.Column('jurisdictions', sa.ARRAY(sa.Text)),
            sa.Column('created_by_user_id', sa.Integer),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.ForeignKeyConstraint(['repository_id'], ['knowledge_schema.repositories.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['collection_id'], ['knowledge_schema.collections.id']),
            schema='knowledge_schema',
        )
        op.create_index('ix_repo_items_repository', 'repository_items', ['repository_id'], schema='knowledge_schema')

    if not inspector.has_table('indexing_runs', schema='knowledge_schema'):
        op.create_table(
            'indexing_runs',
            sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
            sa.Column('repository_id', sa.Integer, nullable=False),
            sa.Column('status', sa.String(20), nullable=False, server_default='running'),
            sa.Column('chunks_indexed', sa.Integer, server_default='0'),
            sa.Column('chunks_skipped', sa.Integer, server_default='0'),
            sa.Column('chunks_expired', sa.Integer, server_default='0'),
            sa.Column('duration_seconds', sa.Float),
            sa.Column('error', sa.Text),
            sa.Column('airflow_dag_run_id', sa.String(255)),
            sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
            sa.Column('completed_at', sa.DateTime(timezone=True)),
            sa.ForeignKeyConstraint(['repository_id'], ['knowledge_schema.repositories.id'], ondelete='CASCADE'),
            schema='knowledge_schema',
        )
        op.create_index('ix_indexing_runs_repository', 'indexing_runs', ['repository_id'], schema='knowledge_schema')


def downgrade() -> None:
    op.execute('DROP TABLE IF EXISTS knowledge_schema.indexing_runs')
    op.execute('DROP TABLE IF EXISTS knowledge_schema.repository_items')
    op.execute('DROP TABLE IF EXISTS knowledge_schema.repositories')
    op.execute('DROP TABLE IF EXISTS knowledge_schema.collections')
