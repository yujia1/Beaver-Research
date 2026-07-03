"""drop_is_verified_column

Revision ID: 5e3be2327443
Revises: c77aaa341f33
Create Date: 2026-07-02 19:07:59.529151

Removes the email-verification-link feature: login is now gated solely by
is_active (admin activation), not is_verified.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '5e3be2327443'
down_revision: Union[str, None] = 'c77aaa341f33'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('users', 'is_verified')


def downgrade() -> None:
    op.add_column('users', sa.Column('is_verified', sa.BOOLEAN(), server_default=sa.false(), autoincrement=False, nullable=True))
