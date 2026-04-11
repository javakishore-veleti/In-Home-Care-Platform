"""create slack_channel_integrations table

Revision ID: 0004
Revises: 0003
Create Date: 2026-04-11

Stores the runtime mapping of (event_type → Slack channel) so admins can
re-route notifications via the care_admin_portal Slack Integrations page
without redeploying or editing env. Lives in member_schema for the same
reason support_cases does: member_svc already owns the alembic runner
and there is no dedicated ops/integrations service yet.
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
    if inspector.has_table('slack_channel_integrations', schema='member_schema'):
        return
    op.create_table(
        'slack_channel_integrations',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('slack_channel_id', sa.String(length=64), nullable=False),
        sa.Column('slack_channel_name', sa.String(length=255), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('enabled', sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('slack_channel_id', 'event_type', name='uq_slack_integration_channel_event'),
        schema='member_schema',
    )
    op.create_index(
        'ix_slack_integrations_event_type',
        'slack_channel_integrations',
        ['event_type'],
        schema='member_schema',
    )


def downgrade() -> None:
    op.execute('DROP INDEX IF EXISTS member_schema.ix_slack_integrations_event_type')
    op.execute('DROP TABLE IF EXISTS member_schema.slack_channel_integrations')
