"""create setup_jobs tracking table

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-11

Tracks admin-triggered bulk operations (Setup Defaults, future re-index-all)
with status, timing, and outcome so the admin UI can show progress and allow
re-runs.
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
    if inspector.has_table('setup_jobs', schema='knowledge_schema'):
        return
    op.create_table(
        'setup_jobs',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('job_type', sa.String(50), nullable=False, server_default='setup_defaults'),
        sa.Column('status', sa.String(20), nullable=False, server_default='running'),
        sa.Column('repos_created', sa.Integer, server_default='0'),
        sa.Column('repos_skipped', sa.Integer, server_default='0'),
        sa.Column('items_created', sa.Integer, server_default='0'),
        sa.Column('error', sa.Text),
        sa.Column('triggered_by_user_id', sa.Integer),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        schema='knowledge_schema',
    )


def downgrade() -> None:
    op.execute('DROP TABLE IF EXISTS knowledge_schema.setup_jobs')
