"""add preferred_llm_model to users

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-12
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
    existing = {c['name'] for c in inspector.get_columns('users', schema='auth_schema')}
    if 'preferred_llm_model' not in existing:
        op.add_column('users', sa.Column('preferred_llm_model', sa.String(50)), schema='auth_schema')


def downgrade() -> None:
    op.execute('ALTER TABLE auth_schema.users DROP COLUMN IF EXISTS preferred_llm_model')
