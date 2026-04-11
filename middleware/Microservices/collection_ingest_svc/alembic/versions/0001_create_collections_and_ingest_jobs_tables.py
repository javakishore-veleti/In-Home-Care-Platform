"""create collections and ingest_jobs tables

Revision ID: 0001
Revises: None
Create Date: 2026-04-10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS collection_schema")
op.execute("SET search_path TO collection_schema")
op.create_table(
    'collections',
    sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
    sa.Column('name', sa.String(200), unique=True, nullable=False),
    sa.Column('description', sa.Text),
    sa.Column('base_path', sa.Text, nullable=False),
    sa.Column('categories', sa.JSON, server_default='[]'),
    sa.Column('created_by', sa.String(100)),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    sa.Column('updated_at', sa.DateTime(timezone=True)),
    schema='collection_schema',
)
op.create_table(
    'ingest_jobs',
    sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
    sa.Column('collection_id', sa.Integer, nullable=False),
    sa.Column('collection_name', sa.String(200)),
    sa.Column('vector_db', sa.String(50), nullable=False),
    sa.Column('status', sa.String(50), server_default='pending'),
    sa.Column('airflow_dag_run_id', sa.String(200)),
    sa.Column('files_total', sa.Integer, server_default='0'),
    sa.Column('files_processed', sa.Integer, server_default='0'),
    sa.Column('files_failed', sa.Integer, server_default='0'),
    sa.Column('error_message', sa.Text),
    sa.Column('requested_by', sa.String(100)),
    sa.Column('requested_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    sa.Column('completed_at', sa.DateTime(timezone=True)),
    schema='collection_schema',
)


def downgrade() -> None:
    op.execute("DROP SCHEMA IF EXISTS collection_schema CASCADE")
