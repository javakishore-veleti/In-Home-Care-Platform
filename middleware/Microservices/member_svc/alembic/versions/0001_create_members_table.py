"""create members table

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
    op.execute("CREATE SCHEMA IF NOT EXISTS member_schema")
op.execute("SET search_path TO member_schema")
op.create_table(
    'members',
    sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
    sa.Column('tenant_id', sa.String(100), nullable=False),
    sa.Column('first_name', sa.String(100)),
    sa.Column('last_name', sa.String(100)),
    sa.Column('email', sa.String(255)),
    sa.Column('phone', sa.String(50)),
    sa.Column('dob', sa.Date),
    sa.Column('address', sa.Text),
    sa.Column('insurance_id', sa.String(100)),
    sa.Column('preferences', sa.JSON, server_default='{}'),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    sa.Column('updated_at', sa.DateTime(timezone=True)),
    schema='member_schema',
)


def downgrade() -> None:
    op.execute("DROP SCHEMA IF EXISTS member_schema CASCADE")
