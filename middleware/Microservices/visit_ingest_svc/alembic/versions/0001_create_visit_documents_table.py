"""create visit_documents table

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
    op.execute("CREATE SCHEMA IF NOT EXISTS visit_ingest_schema")
    op.create_table(
        'visit_documents',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('visit_id', sa.Integer, nullable=False),
        sa.Column('member_id', sa.Integer, nullable=False),
        sa.Column('doc_type', sa.String(50), nullable=False),
        sa.Column('mime_type', sa.String(100)),
        sa.Column('file_path', sa.Text),
        sa.Column('raw_text', sa.Text),
        sa.Column('ocr_confidence', sa.Float),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        schema='visit_ingest_schema',
    )


def downgrade() -> None:
    op.execute("DROP SCHEMA IF EXISTS visit_ingest_schema CASCADE")
