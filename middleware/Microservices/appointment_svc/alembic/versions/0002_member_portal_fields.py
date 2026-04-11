"""extend appointments for member portal

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
    op.add_column('appointments', sa.Column('address_id', sa.Integer(), nullable=True), schema='appointment_schema')
    op.add_column('appointments', sa.Column('scheduled_start', sa.DateTime(timezone=True), nullable=True), schema='appointment_schema')
    op.add_column('appointments', sa.Column('scheduled_end', sa.DateTime(timezone=True), nullable=True), schema='appointment_schema')
    op.add_column('appointments', sa.Column('reason', sa.Text(), nullable=True), schema='appointment_schema')
    op.add_column('appointments', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True), schema='appointment_schema')
    op.execute("UPDATE appointment_schema.appointments SET address_id = 0 WHERE address_id IS NULL")
    op.alter_column('appointments', 'address_id', nullable=False, schema='appointment_schema')
    op.execute("UPDATE appointment_schema.appointments SET updated_at = now() WHERE updated_at IS NULL")


def downgrade() -> None:
    op.drop_column('appointments', 'updated_at', schema='appointment_schema')
    op.drop_column('appointments', 'reason', schema='appointment_schema')
    op.drop_column('appointments', 'scheduled_end', schema='appointment_schema')
    op.drop_column('appointments', 'scheduled_start', schema='appointment_schema')
    op.drop_column('appointments', 'address_id', schema='appointment_schema')
