"""create support_cases table

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-11

Lives in member_schema because cases are keyed on member_id and the
support flow has no service of its own yet. If/when a dedicated
support_svc emerges, the table can be moved out wholesale — nothing
outside member_svc reads it directly today; access goes through the
api_gateway support routes.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0003'
down_revision: Union[str, None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table('support_cases', schema='member_schema'):
        return
    op.create_table(
        'support_cases',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('member_id', sa.Integer, nullable=False),
        sa.Column('subject', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('priority', sa.String(length=20), nullable=False, server_default='medium'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='open'),
        sa.Column('created_by_user_id', sa.Integer, nullable=True),
        sa.Column('assigned_to_user_id', sa.Integer, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        schema='member_schema',
    )
    op.create_index('ix_support_cases_member_id', 'support_cases', ['member_id'], schema='member_schema')
    op.create_index('ix_support_cases_status', 'support_cases', ['status'], schema='member_schema')


def downgrade() -> None:
    op.execute('DROP INDEX IF EXISTS member_schema.ix_support_cases_status')
    op.execute('DROP INDEX IF EXISTS member_schema.ix_support_cases_member_id')
    op.execute('DROP TABLE IF EXISTS member_schema.support_cases')
