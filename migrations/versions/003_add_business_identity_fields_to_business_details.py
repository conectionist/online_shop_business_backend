"""
Add optional merchant identity fields to business_details

Revision ID: 003
Revises: 002
Create Date: 2025-09-03
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('business_details', sa.Column('business_name', sa.String(length=100), nullable=True))
    op.add_column('business_details', sa.Column('registration_number', sa.String(length=20), nullable=True))
    op.add_column('business_details', sa.Column('CUI', sa.String(length=16), nullable=True))
    op.add_column('business_details', sa.Column('email', sa.String(length=100), nullable=True))
    op.add_column('business_details', sa.Column('operating_hours', sa.String(length=150), nullable=True))
    op.add_column('business_details', sa.Column('representative', sa.String(length=100), nullable=True))


def downgrade() -> None:
    op.drop_column('business_details', 'representative')
    op.drop_column('business_details', 'operating_hours')
    op.drop_column('business_details', 'email')
    op.drop_column('business_details', 'CUI')
    op.drop_column('business_details', 'registration_number')
    op.drop_column('business_details', 'business_name')


