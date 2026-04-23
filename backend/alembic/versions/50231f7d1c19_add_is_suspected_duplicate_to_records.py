"""add is_suspected_duplicate to records

Revision ID: 50231f7d1c19
Revises: 10634eba643d
Create Date: 2026-04-23 10:27:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '50231f7d1c19'
down_revision = '10634eba643d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if column exists before adding (idempotent)
    conn = op.get_bind()
    result = conn.execute(
        sa.text("SELECT 1 FROM information_schema.columns WHERE table_name='records' AND column_name='is_suspected_duplicate'")
    )
    if not result.fetchone():
        op.add_column('records', sa.Column('is_suspected_duplicate', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('records', 'is_suspected_duplicate')
