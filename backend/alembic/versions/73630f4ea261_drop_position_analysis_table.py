"""drop_position_analysis_table

Revision ID: 73630f4ea261
Revises: 5e3be2327443
Create Date: 2026-07-03 16:41:20.499268

Removes the Fundamental Analysis feature: the position_analysis table backed
the per-question answer/score data for the (now removed) Fundamental
Analysis tab on the Portfolio page.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '73630f4ea261'
down_revision: Union[str, None] = '5e3be2327443'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index('ix_position_analysis_id', table_name='position_analysis')
    op.drop_index('ix_position_analysis_position_id', table_name='position_analysis')
    op.drop_table('position_analysis')


def downgrade() -> None:
    op.create_table('position_analysis',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('position_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('question_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('answer', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('score', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['position_id'], ['portfolio_positions.id'], name='position_analysis_position_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='position_analysis_pkey'),
    sa.UniqueConstraint('position_id', 'question_id', name='uix_position_question')
    )
    op.create_index('ix_position_analysis_position_id', 'position_analysis', ['position_id'], unique=False)
    op.create_index('ix_position_analysis_id', 'position_analysis', ['id'], unique=False)
