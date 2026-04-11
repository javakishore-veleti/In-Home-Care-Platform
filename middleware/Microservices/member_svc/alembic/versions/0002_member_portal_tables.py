"""add member portal tables

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
    op.add_column('members', sa.Column('user_id', sa.Integer(), nullable=True), schema='member_schema')
    op.create_unique_constraint('uq_members_user_id', 'members', ['user_id'], schema='member_schema')
    op.create_table(
        'member_addresses',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('member_id', sa.Integer(), nullable=False),
        sa.Column('label', sa.String(length=100), nullable=False, server_default='Home'),
        sa.Column('line1', sa.String(length=255), nullable=False),
        sa.Column('line2', sa.String(length=255), nullable=True),
        sa.Column('city', sa.String(length=120), nullable=False),
        sa.Column('state', sa.String(length=120), nullable=False),
        sa.Column('postal_code', sa.String(length=20), nullable=False),
        sa.Column('instructions', sa.Text(), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        schema='member_schema',
    )
    op.create_table(
        'member_chat_messages',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('member_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        schema='member_schema',
    )


def downgrade() -> None:
    op.drop_table('member_chat_messages', schema='member_schema')
    op.drop_table('member_addresses', schema='member_schema')
    op.drop_constraint('uq_members_user_id', 'members', schema='member_schema', type_='unique')
    op.drop_column('members', 'user_id', schema='member_schema')
