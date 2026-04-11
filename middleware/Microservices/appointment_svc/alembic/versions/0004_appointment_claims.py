"""appointment claims via Slack

Revision ID: 0004
Revises: 0003
Create Date: 2026-04-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0004'
down_revision: Union[str, None] = '0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    existing_columns = {column['name'] for column in inspector.get_columns('appointments', schema='appointment_schema')}
    if 'slack_message_ts' not in existing_columns:
        op.add_column(
            'appointments',
            sa.Column('slack_message_ts', sa.String(length=64), nullable=True),
            schema='appointment_schema',
        )
    if 'slack_channel_id' not in existing_columns:
        op.add_column(
            'appointments',
            sa.Column('slack_channel_id', sa.String(length=64), nullable=True),
            schema='appointment_schema',
        )

    if not inspector.has_table('appointment_claims', schema='appointment_schema'):
        op.create_table(
            'appointment_claims',
            sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
            sa.Column('appointment_id', sa.Integer, nullable=False),
            sa.Column('slack_user_id', sa.String(length=64), nullable=False),
            sa.Column('slack_user_name', sa.String(length=255)),
            sa.Column('slack_team_id', sa.String(length=64)),
            sa.Column('slack_channel_id', sa.String(length=64)),
            sa.Column('slack_message_ts', sa.String(length=64)),
            sa.Column('claimed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(
                ['appointment_id'],
                ['appointment_schema.appointments.id'],
                ondelete='CASCADE',
            ),
            sa.UniqueConstraint('appointment_id', name='uq_appointment_claims_appointment_id'),
            schema='appointment_schema',
        )
        op.create_index(
            'ix_appointment_claims_slack_user_id',
            'appointment_claims',
            ['slack_user_id'],
            schema='appointment_schema',
        )


def downgrade() -> None:
    op.execute('DROP INDEX IF EXISTS appointment_schema.ix_appointment_claims_slack_user_id')
    op.execute('DROP TABLE IF EXISTS appointment_schema.appointment_claims')
    op.execute('ALTER TABLE appointment_schema.appointments DROP COLUMN IF EXISTS slack_channel_id')
    op.execute('ALTER TABLE appointment_schema.appointments DROP COLUMN IF EXISTS slack_message_ts')
