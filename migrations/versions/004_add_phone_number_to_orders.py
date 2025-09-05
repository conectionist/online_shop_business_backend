"""Add phone_number field to orders table

Revision ID: 004
Revises: 003
Create Date: 2025-01-XX 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    """Add phone_number column to comenzi table"""
    
    # Add phone_number column to comenzi table
    op.add_column('comenzi', sa.Column('phone_number', sa.String(20), nullable=True))
    
    # Add index for performance (optional, but good practice for searchable fields)
    op.create_index('idx_comenzi_phone_number', 'comenzi', ['phone_number'])


def downgrade():
    """Remove phone_number column from comenzi table"""
    
    # Remove index
    op.drop_index('idx_comenzi_phone_number', table_name='comenzi')
    
    # Remove column
    op.drop_column('comenzi', 'phone_number')
