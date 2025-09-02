"""
Add delivery_tax column to business_details

Revision ID: 002
Revises: 001
Create Date: 2025-09-02
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'business_details',
        sa.Column('delivery_tax', sa.SmallInteger(), nullable=True, server_default='0')
    )


def downgrade() -> None:
    op.drop_column('business_details', 'delivery_tax')


