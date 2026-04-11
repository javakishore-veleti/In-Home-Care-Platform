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
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = {column['name'] for column in inspector.get_columns('appointments', schema='appointment_schema')}

    if 'address_id' not in existing_columns:
        op.add_column('appointments', sa.Column('address_id', sa.Integer(), nullable=True), schema='appointment_schema')
    if 'scheduled_start' not in existing_columns:
        op.add_column('appointments', sa.Column('scheduled_start', sa.DateTime(timezone=True), nullable=True), schema='appointment_schema')
    if 'scheduled_end' not in existing_columns:
        op.add_column('appointments', sa.Column('scheduled_end', sa.DateTime(timezone=True), nullable=True), schema='appointment_schema')
    if 'reason' not in existing_columns:
        op.add_column('appointments', sa.Column('reason', sa.Text(), nullable=True), schema='appointment_schema')
    if 'updated_at' not in existing_columns:
        op.add_column('appointments', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True), schema='appointment_schema')

    refreshed_columns = {column['name']: column for column in inspector.get_columns('appointments', schema='appointment_schema')}
    if 'address_id' in refreshed_columns:
        op.execute("UPDATE appointment_schema.appointments SET address_id = 0 WHERE address_id IS NULL")
        if refreshed_columns['address_id'].get('nullable', True):
            op.alter_column('appointments', 'address_id', nullable=False, schema='appointment_schema')
    if 'updated_at' in refreshed_columns:
        op.execute("UPDATE appointment_schema.appointments SET updated_at = now() WHERE updated_at IS NULL")


def downgrade() -> None:
    op.execute('ALTER TABLE appointment_schema.appointments DROP COLUMN IF EXISTS updated_at')
    op.execute('ALTER TABLE appointment_schema.appointments DROP COLUMN IF EXISTS reason')
    op.execute('ALTER TABLE appointment_schema.appointments DROP COLUMN IF EXISTS scheduled_end')
    op.execute('ALTER TABLE appointment_schema.appointments DROP COLUMN IF EXISTS scheduled_start')
    op.execute('ALTER TABLE appointment_schema.appointments DROP COLUMN IF EXISTS address_id')
