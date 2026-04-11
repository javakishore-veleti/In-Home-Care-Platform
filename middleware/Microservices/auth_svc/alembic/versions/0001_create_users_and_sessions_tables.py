"""create users and sessions tables

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
    op.execute("CREATE SCHEMA IF NOT EXISTS auth_schema")
op.execute("SET search_path TO auth_schema")
op.create_table(
    'users',
    sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
    sa.Column('email', sa.String(255), unique=True, nullable=False),
    sa.Column('hashed_password', sa.String(255), nullable=False),
    sa.Column('role', sa.String(50), nullable=False, server_default='member'),
    sa.Column('is_active', sa.Boolean, server_default='true'),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    schema='auth_schema',
)
op.create_table(
    'sessions',
    sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
    sa.Column('user_id', sa.Integer, nullable=False),
    sa.Column('token_hash', sa.String(255), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    schema='auth_schema',
)


def downgrade() -> None:
    op.execute("DROP SCHEMA IF EXISTS auth_schema CASCADE")
