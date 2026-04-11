"""appointment_slack_posts: per-channel slack-post dedupe

Revision ID: 0005
Revises: 0004
Create Date: 2026-04-11

When slack_svc fans an appointment.booked event out to multiple Slack
channels (because the admin wired the same event_type to more than one
channel via the Slack Integrations page), each channel needs its own
dedupe key — the legacy `appointments.slack_message_ts` column can only
hold one ts.

This table records every successful chat.postMessage so that on a
Kafka redelivery, slack_svc can per-channel ask "have I already posted
to this channel for this appointment?" and skip the ones it has.

The legacy `slack_channel_id` / `slack_message_ts` columns on
`appointments` are intentionally left in place for backwards
compatibility with the admin detail page; the store updates both the
new table and (only on first post) the legacy columns.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0005'
down_revision: Union[str, None] = '0004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table('appointment_slack_posts', schema='appointment_schema'):
        return
    op.create_table(
        'appointment_slack_posts',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('appointment_id', sa.Integer, nullable=False),
        sa.Column('slack_channel_id', sa.String(length=64), nullable=False),
        sa.Column('slack_message_ts', sa.String(length=64), nullable=False),
        sa.Column('posted_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(
            ['appointment_id'],
            ['appointment_schema.appointments.id'],
            ondelete='CASCADE',
        ),
        sa.UniqueConstraint('appointment_id', 'slack_channel_id', name='uq_appointment_slack_post_channel'),
        schema='appointment_schema',
    )
    op.create_index(
        'ix_appointment_slack_posts_appointment_id',
        'appointment_slack_posts',
        ['appointment_id'],
        schema='appointment_schema',
    )


def downgrade() -> None:
    op.execute('DROP INDEX IF EXISTS appointment_schema.ix_appointment_slack_posts_appointment_id')
    op.execute('DROP TABLE IF EXISTS appointment_schema.appointment_slack_posts')
