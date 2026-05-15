"""Add exchange_rates table

Revision ID: a1b2c3d4e5f6
Revises: 10634eba643d
Create Date: 2026-05-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '10634eba643d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add exchange_rates table for user-customizable currency rates."""
    op.create_table(
        'exchange_rates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False),
        sa.Column('rate', sa.Float(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'currency', name='uq_user_currency'),
    )
    op.create_index(op.f('ix_exchange_rates_id'), 'exchange_rates', ['id'], unique=False)


def downgrade() -> None:
    """Remove exchange_rates table."""
    op.drop_index(op.f('ix_exchange_rates_id'), table_name='exchange_rates')
    op.drop_table('exchange_rates')
