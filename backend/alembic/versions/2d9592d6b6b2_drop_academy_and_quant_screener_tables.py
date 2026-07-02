"""drop_academy_and_quant_screener_tables

Revision ID: 2d9592d6b6b2
Revises: 5135e29cfa34
Create Date: 2026-07-02 00:30:39.908577

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2d9592d6b6b2'
down_revision: Union[str, None] = '5135e29cfa34'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drops the quant screener tables backing the deleted /quant feature.
    # Also removes leftover /academy and /quant role_permissions rows, since
    # those resources no longer exist in the app.
    op.drop_index('ix_flagged_companies_id', table_name='flagged_companies')
    op.drop_index('ix_flagged_companies_screening_date', table_name='flagged_companies')
    op.drop_index('ix_flagged_companies_screening_run_id', table_name='flagged_companies')
    op.drop_index('ix_flagged_companies_ticker', table_name='flagged_companies')
    op.drop_table('flagged_companies')
    op.drop_index('ix_screening_runs_id', table_name='screening_runs')
    op.drop_index('ix_screening_runs_run_date', table_name='screening_runs')
    op.drop_table('screening_runs')
    op.drop_index('ix_stock_universe_id', table_name='stock_universe')
    op.drop_index('ix_stock_universe_ticker', table_name='stock_universe')
    op.drop_table('stock_universe')

    op.execute("DELETE FROM role_permissions WHERE resource IN ('/academy', '/quant')")


def downgrade() -> None:
    op.create_table('stock_universe',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('ticker', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('company_name', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('exchange', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('sector', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('industry', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('market_cap', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('is_active', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('last_updated', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='stock_universe_pkey')
    )
    op.create_index('ix_stock_universe_ticker', 'stock_universe', ['ticker'], unique=True)
    op.create_index('ix_stock_universe_id', 'stock_universe', ['id'], unique=False)
    op.create_table('screening_runs',
    sa.Column('id', sa.INTEGER(), server_default=sa.text("nextval('screening_runs_id_seq'::regclass)"), autoincrement=True, nullable=False),
    sa.Column('run_date', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.Column('target_total_stocks', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('total_stocks_processed', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('total_flagged', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('strategies_run', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=False),
    sa.Column('status', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('error_log', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('duration_seconds', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('completed_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='screening_runs_pkey'),
    postgresql_ignore_search_path=False
    )
    op.create_index('ix_screening_runs_run_date', 'screening_runs', ['run_date'], unique=False)
    op.create_index('ix_screening_runs_id', 'screening_runs', ['id'], unique=False)
    op.create_table('flagged_companies',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('ticker', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('company_name', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('sector', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('screening_run_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('screening_date', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.Column('strategies_flagged', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=False),
    sa.Column('metrics', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=False),
    sa.Column('red_flags', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=False),
    sa.Column('financial_data', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['screening_run_id'], ['screening_runs.id'], name='flagged_companies_screening_run_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='flagged_companies_pkey'),
    sa.UniqueConstraint('ticker', 'screening_date', name='uix_ticker_screening_date')
    )
    op.create_index('ix_flagged_companies_ticker', 'flagged_companies', ['ticker'], unique=False)
    op.create_index('ix_flagged_companies_screening_run_id', 'flagged_companies', ['screening_run_id'], unique=False)
    op.create_index('ix_flagged_companies_screening_date', 'flagged_companies', ['screening_date'], unique=False)
    op.create_index('ix_flagged_companies_id', 'flagged_companies', ['id'], unique=False)
    # Note: role_permissions rows deleted in upgrade() are not restored here,
    # since they'll be reseeded automatically by the app's startup permission
    # initialization the next time it boots.
