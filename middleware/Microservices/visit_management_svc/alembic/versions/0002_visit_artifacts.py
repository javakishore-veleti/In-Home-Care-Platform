"""add visit artifact tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0002'
down_revision: Union[str, None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'visit_documents',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('visit_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('doc_type', sa.String(length=100), nullable=False),
        sa.Column('mime_type', sa.String(length=120), nullable=True),
        sa.Column('file_path', sa.Text(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        schema='visit_schema',
    )
    op.create_table(
        'visit_notes',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('visit_id', sa.Integer(), nullable=False),
        sa.Column('note', sa.Text(), nullable=False),
        sa.Column('author_name', sa.String(length=120), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        schema='visit_schema',
    )
    op.create_table(
        'visit_decisions',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('visit_id', sa.Integer(), nullable=False),
        sa.Column('decision', sa.Text(), nullable=False),
        sa.Column('owner_name', sa.String(length=120), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        schema='visit_schema',
    )
    op.create_table(
        'visit_action_items',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('visit_id', sa.Integer(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(length=40), nullable=False, server_default='open'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        schema='visit_schema',
    )


def downgrade() -> None:
    op.drop_table('visit_action_items', schema='visit_schema')
    op.drop_table('visit_decisions', schema='visit_schema')
    op.drop_table('visit_notes', schema='visit_schema')
    op.drop_table('visit_documents', schema='visit_schema')
