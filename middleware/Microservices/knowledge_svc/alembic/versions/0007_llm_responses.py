"""create llm_responses table

Revision ID: 0007
Revises: 0006
Create Date: 2026-04-12

Stores every LLM response for every appointment claim — one row per
model. Enables side-by-side comparison, token cost tracking, and the
feedback loop (thumbs up/down).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0007'
down_revision: Union[str, None] = '0006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table('llm_responses', schema='knowledge_schema'):
        return
    op.create_table(
        'llm_responses',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('appointment_id', sa.Integer, nullable=False),
        sa.Column('model_id', sa.String(50), nullable=False),
        sa.Column('provider', sa.String(30), nullable=False),
        sa.Column('display_name', sa.String(100)),
        sa.Column('system_prompt', sa.Text),
        sa.Column('user_prompt', sa.Text, nullable=False),
        sa.Column('rag_chunks_used', sa.Integer, server_default='0'),
        sa.Column('response_text', sa.Text, nullable=False),
        sa.Column('finish_reason', sa.String(30)),
        sa.Column('input_tokens', sa.Integer, nullable=False, server_default='0'),
        sa.Column('output_tokens', sa.Integer, nullable=False, server_default='0'),
        sa.Column('total_tokens', sa.Integer, nullable=False, server_default='0'),
        sa.Column('input_cost_usd', sa.Numeric(10, 6), server_default='0'),
        sa.Column('output_cost_usd', sa.Numeric(10, 6), server_default='0'),
        sa.Column('total_cost_usd', sa.Numeric(10, 6), server_default='0'),
        sa.Column('latency_ms', sa.Integer),
        sa.Column('is_primary', sa.Boolean, server_default=sa.false()),
        sa.Column('rating', sa.SmallInteger),
        sa.Column('rating_comment', sa.Text),
        sa.Column('service_type', sa.String(100)),
        sa.Column('collection_slug', sa.String(255)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        schema='knowledge_schema',
    )
    op.create_index('ix_llm_responses_appointment', 'llm_responses', ['appointment_id'], schema='knowledge_schema')
    op.create_index('ix_llm_responses_model', 'llm_responses', ['model_id'], schema='knowledge_schema')


def downgrade() -> None:
    op.execute('DROP INDEX IF EXISTS knowledge_schema.ix_llm_responses_model')
    op.execute('DROP INDEX IF EXISTS knowledge_schema.ix_llm_responses_appointment')
    op.execute('DROP TABLE IF EXISTS knowledge_schema.llm_responses')
