"""create extracted_fields table

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
    op.execute("CREATE SCHEMA IF NOT EXISTS doc_intel_schema")
op.execute("SET search_path TO doc_intel_schema")
op.create_table(
    'extracted_fields',
    sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
    sa.Column('document_id', sa.Integer, nullable=False),
    sa.Column('field_name', sa.String(200), nullable=False),
    sa.Column('field_value', sa.Text),
    sa.Column('confidence', sa.Float),
    sa.Column('is_pii', sa.Boolean, server_default='false'),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    schema='doc_intel_schema',
)


def downgrade() -> None:
    op.execute("DROP SCHEMA IF EXISTS doc_intel_schema CASCADE")
