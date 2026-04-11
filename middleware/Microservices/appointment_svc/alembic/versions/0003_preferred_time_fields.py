"""add preferred appointment time fields

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-11
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
    existing_columns = {column['name'] for column in inspector.get_columns('appointments', schema='appointment_schema')}

    if 'preferred_hour' not in existing_columns:
        op.add_column('appointments', sa.Column('preferred_hour', sa.String(length=2), nullable=True), schema='appointment_schema')
    if 'preferred_minute' not in existing_columns:
        op.add_column('appointments', sa.Column('preferred_minute', sa.String(length=2), nullable=True), schema='appointment_schema')


def downgrade() -> None:
    op.execute('ALTER TABLE appointment_schema.appointments DROP COLUMN IF EXISTS preferred_minute')
    op.execute('ALTER TABLE appointment_schema.appointments DROP COLUMN IF EXISTS preferred_hour')
