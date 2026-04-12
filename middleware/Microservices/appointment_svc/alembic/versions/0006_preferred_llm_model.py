"""add preferred_llm_model to appointments

Revision ID: 0006
Revises: 0005
Create Date: 2026-04-12
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0006'
down_revision: Union[str, None] = '0005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = {c['name'] for c in inspector.get_columns('appointments', schema='appointment_schema')}
    if 'preferred_llm_model' not in existing:
        op.add_column('appointments', sa.Column('preferred_llm_model', sa.String(50)), schema='appointment_schema')


def downgrade() -> None:
    op.execute('ALTER TABLE appointment_schema.appointments DROP COLUMN IF EXISTS preferred_llm_model')
