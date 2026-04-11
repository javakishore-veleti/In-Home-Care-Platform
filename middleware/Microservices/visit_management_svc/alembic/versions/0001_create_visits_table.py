"""create visits table

Revision ID: 0001
Revises: None
Create Date: 2026-04-10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE SCHEMA IF NOT EXISTS visit_schema')
    op.create_table(
        'visits',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('member_id', sa.Integer, nullable=False),
        sa.Column('appointment_id', sa.Integer),
        sa.Column('staff_id', sa.Integer),
        sa.Column('visit_date', sa.Date),
        sa.Column('status', sa.String(50), server_default='scheduled'),
        sa.Column('started_at', sa.DateTime(timezone=True)),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('notes_summary', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        schema='visit_schema',
    )


def downgrade() -> None:
    op.drop_table('visits', schema='visit_schema')
