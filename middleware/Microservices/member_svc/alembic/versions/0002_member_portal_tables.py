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
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names(schema='member_schema'))
    member_columns = {column['name'] for column in inspector.get_columns('members', schema='member_schema')}
    member_constraints = {constraint['name'] for constraint in inspector.get_unique_constraints('members', schema='member_schema')}

    if 'user_id' not in member_columns:
        op.add_column('members', sa.Column('user_id', sa.Integer(), nullable=True), schema='member_schema')
    if 'uq_members_user_id' not in member_constraints:
        op.create_unique_constraint('uq_members_user_id', 'members', ['user_id'], schema='member_schema')
    if 'member_addresses' not in existing_tables:
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
    if 'member_chat_messages' not in existing_tables:
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
    op.execute('DROP TABLE IF EXISTS member_schema.member_chat_messages')
    op.execute('DROP TABLE IF EXISTS member_schema.member_addresses')
    op.execute('ALTER TABLE member_schema.members DROP CONSTRAINT IF EXISTS uq_members_user_id')
    op.execute('ALTER TABLE member_schema.members DROP COLUMN IF EXISTS user_id')
