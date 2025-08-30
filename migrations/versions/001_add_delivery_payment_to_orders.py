"""Add delivery and payment method fields to orders table

Revision ID: 001
Revises: 
Create Date: 2025-01-XX 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Add delivery and payment method fields to comenzi table"""
    
    # Add new columns to comenzi table
    op.add_column('comenzi', sa.Column('delivery_type_id', mysql.TINYINT(), nullable=False))
    op.add_column('comenzi', sa.Column('payment_method_id', sa.Integer(), nullable=False))
    op.add_column('comenzi', sa.Column('delivery_address', sa.String(150), nullable=True))
    
    # Add indexes for performance
    op.create_index('idx_comenzi_delivery_type', 'comenzi', ['delivery_type_id'])
    op.create_index('idx_comenzi_payment_method', 'comenzi', ['payment_method_id'])
    op.create_index('idx_comenzi_delivery_address', 'comenzi', ['delivery_address'])
    
    # Add foreign key constraints
    op.create_foreign_key(
        'fk_comenzi_delivery_type',
        'comenzi', 'tipuri_livrare',
        ['delivery_type_id'], ['id'],
        ondelete='RESTRICT',
        onupdate='CASCADE'
    )
    op.create_foreign_key(
        'fk_comenzi_payment_method',
        'comenzi', 'modalitati_de_plata',
        ['payment_method_id'], ['id'],
        ondelete='RESTRICT',
        onupdate='CASCADE'
    )


def downgrade():
    """Remove delivery and payment method fields from comenzi table"""
    
    # Remove foreign key constraints
    op.drop_constraint('fk_comenzi_payment_method', 'comenzi', type_='foreignkey')
    op.drop_constraint('fk_comenzi_delivery_type', 'comenzi', type_='foreignkey')
    
    # Remove indexes
    op.drop_index('idx_comenzi_delivery_address', table_name='comenzi')
    op.drop_index('idx_comenzi_payment_method', table_name='comenzi')
    op.drop_index('idx_comenzi_delivery_type', table_name='comenzi')
    
    # Remove columns
    op.drop_column('comenzi', 'delivery_address')
    op.drop_column('comenzi', 'payment_method_id')
    op.drop_column('comenzi', 'delivery_type_id')
