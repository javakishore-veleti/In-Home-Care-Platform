"""create appointments table

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
    op.execute('CREATE SCHEMA IF NOT EXISTS appointment_schema')
    op.create_table(
        'appointments',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('member_id', sa.Integer, nullable=False),
        sa.Column('service_type', sa.String(100), nullable=False),
        sa.Column('service_area', sa.String(100)),
        sa.Column('requested_date', sa.Date, nullable=False),
        sa.Column('requested_time_slot', sa.String(50)),
        sa.Column('status', sa.String(50), server_default='pending'),
        sa.Column('assigned_staff_id', sa.Integer),
        sa.Column('notes', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('cancelled_at', sa.DateTime(timezone=True)),
        schema='appointment_schema',
    )


def downgrade() -> None:
    op.drop_table('appointments', schema='appointment_schema')
