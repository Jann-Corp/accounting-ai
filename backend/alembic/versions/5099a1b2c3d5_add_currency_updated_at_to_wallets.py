"""add currency and updated_at to wallets

Revision ID: 5099a1b2c3d5
Revises: 50231f7d1c19
Create Date: 2026-05-11 18:46:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5099a1b2c3d5'
down_revision: Union[str, Sequence[str], None] = '50231f7d1c19'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add currency and updated_at columns to wallets table."""
    with op.batch_alter_table('wallets', schema=None) as batch_op:
        batch_op.add_column(sa.Column('currency', sa.String(length=10), nullable=True))
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Remove currency and updated_at columns from wallets table."""
    with op.batch_alter_table('wallets', schema=None) as batch_op:
        batch_op.drop_column('updated_at')
        batch_op.drop_column('currency')
