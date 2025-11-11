"""Add payment_type_id and required_data to modalitati_de_plata table

Revision ID: 015
Revises: 014
Create Date: 2025-11-06 18:40

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '015'
down_revision = '014'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add payment_type_id and required_data columns to modalitati_de_plata table"""
    
    connection = op.get_bind()
    inspector = inspect(connection)
    
    # Check if table exists
    if 'modalitati_de_plata' not in inspector.get_table_names():
        return
    
    # Get existing columns
    existing_columns = {col['name'] for col in inspector.get_columns('modalitati_de_plata')}
    existing_indexes = {idx['name'] for idx in inspector.get_indexes('modalitati_de_plata')}
    existing_fks = {fk['name'] for fk in inspector.get_foreign_keys('modalitati_de_plata')}
    
    # Add payment_type_id column (default 0 for existing rows)
    if 'payment_type_id' not in existing_columns:
        op.add_column('modalitati_de_plata', 
            sa.Column('payment_type_id', sa.Integer(), nullable=True, server_default='0'))
        # Update all existing rows to have payment_type_id = 0 (custom)
        connection.execute(sa.text(
            "UPDATE modalitati_de_plata SET payment_type_id = 0 WHERE payment_type_id IS NULL"
        ))
        # Now make it NOT NULL
        op.alter_column('modalitati_de_plata', 'payment_type_id',
                       existing_type=sa.Integer(),
                       nullable=False,
                       server_default=None)
    
    # Add required_data JSON column (nullable)
    if 'required_data' not in existing_columns:
        op.add_column('modalitati_de_plata',
            sa.Column('required_data', mysql.JSON, nullable=True))
    
    # Add index on payment_type_id
    if 'idx_modalitati_plata_payment_type' not in existing_indexes:
        op.create_index('idx_modalitati_plata_payment_type', 'modalitati_de_plata', ['payment_type_id'])
    
    # Add foreign key constraint
    if 'fk_modalitati_plata_payment_type' not in existing_fks:
        op.create_foreign_key(
            'fk_modalitati_plata_payment_type',
            'modalitati_de_plata', 'payment_types',
            ['payment_type_id'], ['id'],
            ondelete='RESTRICT', onupdate='CASCADE'
        )


def downgrade() -> None:
    """Remove payment_type_id and required_data columns from modalitati_de_plata table"""
    
    # Remove foreign key constraint
    op.drop_constraint('fk_modalitati_plata_payment_type', 'modalitati_de_plata', type_='foreignkey')
    
    # Remove index
    op.drop_index('idx_modalitati_plata_payment_type', table_name='modalitati_de_plata')
    
    # Remove columns
    op.drop_column('modalitati_de_plata', 'required_data')
    op.drop_column('modalitati_de_plata', 'payment_type_id')

