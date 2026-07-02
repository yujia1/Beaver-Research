"""redesign_portfolio_as_shared_entity

Revision ID: e3fec0585ae6
Revises: 2d9592d6b6b2
Create Date: 2026-07-02 14:05:10.782071

Portfolio moves from one-portfolio-per-user to a single shared portfolio:
positions are now unique by ticker alone (not ticker+user), and gain an
updated_by_user_id audit column instead of an owning user_id. Per product
decision, this wipes existing portfolio data rather than attempting to
merge/reconcile per-user positions into the new shared schema.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'e3fec0585ae6'
down_revision: Union[str, None] = '2d9592d6b6b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Wipe existing per-user portfolio data before reshaping the schema, since
    # there's no sound way to auto-merge separate users' positions in the same
    # ticker into one shared position.
    op.execute("TRUNCATE TABLE portfolio_lots, position_analysis, portfolio_positions RESTART IDENTITY CASCADE")

    op.add_column('portfolio_lots', sa.Column('updated_by_user_id', sa.Integer(), nullable=True))
    op.add_column('portfolio_lots', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True))
    op.create_index(op.f('ix_portfolio_lots_updated_by_user_id'), 'portfolio_lots', ['updated_by_user_id'], unique=False)
    op.create_foreign_key(None, 'portfolio_lots', 'users', ['updated_by_user_id'], ['id'])

    op.add_column('portfolio_positions', sa.Column('updated_by_user_id', sa.Integer(), nullable=True))
    op.drop_index('ix_portfolio_positions_user_id', table_name='portfolio_positions')
    op.drop_constraint('uix_user_ticker_portfolio', 'portfolio_positions', type_='unique')
    op.drop_index('ix_portfolio_positions_ticker', table_name='portfolio_positions')
    op.create_index(op.f('ix_portfolio_positions_ticker'), 'portfolio_positions', ['ticker'], unique=True)
    op.create_index(op.f('ix_portfolio_positions_updated_by_user_id'), 'portfolio_positions', ['updated_by_user_id'], unique=False)
    op.drop_constraint('portfolio_positions_user_id_fkey', 'portfolio_positions', type_='foreignkey')
    op.create_foreign_key(None, 'portfolio_positions', 'users', ['updated_by_user_id'], ['id'])
    op.drop_column('portfolio_positions', 'user_id')


def downgrade() -> None:
    # Lossy: reverting the shared portfolio back to per-user ownership has no
    # sound way to reassign existing shared positions to a single user, so
    # this also wipes portfolio data.
    op.execute("TRUNCATE TABLE portfolio_lots, position_analysis, portfolio_positions RESTART IDENTITY CASCADE")

    op.add_column('portfolio_positions', sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=False))
    op.drop_constraint(None, 'portfolio_positions', type_='foreignkey')
    op.create_foreign_key('portfolio_positions_user_id_fkey', 'portfolio_positions', 'users', ['user_id'], ['id'])
    op.drop_index(op.f('ix_portfolio_positions_updated_by_user_id'), table_name='portfolio_positions')
    op.drop_index(op.f('ix_portfolio_positions_ticker'), table_name='portfolio_positions')
    op.create_index('ix_portfolio_positions_ticker', 'portfolio_positions', ['ticker'], unique=False)
    op.create_unique_constraint('uix_user_ticker_portfolio', 'portfolio_positions', ['user_id', 'ticker'])
    op.create_index('ix_portfolio_positions_user_id', 'portfolio_positions', ['user_id'], unique=False)
    op.drop_column('portfolio_positions', 'updated_by_user_id')

    op.drop_constraint(None, 'portfolio_lots', type_='foreignkey')
    op.drop_index(op.f('ix_portfolio_lots_updated_by_user_id'), table_name='portfolio_lots')
    op.drop_column('portfolio_lots', 'updated_at')
    op.drop_column('portfolio_lots', 'updated_by_user_id')
