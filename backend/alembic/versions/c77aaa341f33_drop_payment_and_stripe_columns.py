"""drop_payment_and_stripe_columns

Revision ID: c77aaa341f33
Revises: e3fec0585ae6
Create Date: 2026-07-02 14:49:35.391521

Removes the Stripe/payment feature entirely: drops the six payment/billing
columns from users. Access to every resource is now purely role-based.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c77aaa341f33'
down_revision: Union[str, None] = 'e3fec0585ae6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index('ix_users_stripe_customer_id', table_name='users')
    op.drop_column('users', 'stripe_customer_id')
    op.drop_column('users', 'payment_transaction_id')
    op.drop_column('users', 'stripe_subscription_id')
    op.drop_column('users', 'stripe_current_period_end')
    op.drop_column('users', 'has_paid')
    op.drop_column('users', 'payment_date')


def downgrade() -> None:
    op.add_column('users', sa.Column('payment_date', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True))
    op.add_column('users', sa.Column('has_paid', sa.BOOLEAN(), server_default=sa.false(), autoincrement=False, nullable=False))
    op.add_column('users', sa.Column('stripe_current_period_end', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True))
    op.add_column('users', sa.Column('stripe_subscription_id', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('users', sa.Column('payment_transaction_id', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('users', sa.Column('stripe_customer_id', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.create_index('ix_users_stripe_customer_id', 'users', ['stripe_customer_id'], unique=False)
