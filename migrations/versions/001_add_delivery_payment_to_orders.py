"""Add delivery and payment method fields to orders table

Revision ID: 001
Revises: 000_initial_schema
Create Date: 2025-01-XX 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '001'
down_revision = '000_initial_schema'
branch_labels = None
depends_on = None


def upgrade():
    """Add delivery and payment method fields to comenzi table"""
    
    connection = op.get_bind()
    inspector = inspect(connection)
    
    # Create table if it doesn't exist
    if 'comenzi' not in inspector.get_table_names():
        op.create_table('comenzi',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('nume_client', sa.String(50), nullable=False),
            sa.Column('data_plasarii', sa.DateTime(), nullable=False),
            sa.Column('liste_id', sa.Integer(), nullable=False),
            sa.Column('order_notes', sa.String(500), nullable=True),
            sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('id', name='id_UNIQUE'),
            sa.ForeignKeyConstraint(['liste_id'], ['liste.id'], name='fk_comenzi_liste1'),
            sa.Index('idx_comenzi_data_plasarii', 'data_plasarii'),
            sa.Index('idx_comenzi_nume_client', 'nume_client')
        )
    
    # Get all existing database objects in one go
    existing_columns = {col['name'] for col in inspector.get_columns('comenzi')}
    existing_indexes = {idx['name'] for idx in inspector.get_indexes('comenzi')}
    existing_fks = {fk['name'] for fk in inspector.get_foreign_keys('comenzi')}
    
    # Define columns to add
    columns_to_add = [
        ('delivery_type_id', sa.Column('delivery_type_id', mysql.TINYINT(), nullable=False)),
        ('payment_method_id', sa.Column('payment_method_id', sa.Integer(), nullable=False)),
        ('delivery_address', sa.Column('delivery_address', sa.String(150), nullable=True))
    ]
    
    # Add missing columns
    for col_name, column_def in columns_to_add:
        if col_name not in existing_columns:
            op.add_column('comenzi', column_def)
    
    # Define indexes to add
    indexes_to_add = [
        ('idx_comenzi_delivery_type', ['delivery_type_id']),
        ('idx_comenzi_payment_method', ['payment_method_id']),
        ('idx_comenzi_delivery_address', ['delivery_address'])
    ]
    
    # Add missing indexes
    for idx_name, columns in indexes_to_add:
        if idx_name not in existing_indexes:
            op.create_index(idx_name, 'comenzi', columns)
    
    # Define foreign keys to add
    foreign_keys_to_add = [
        ('fk_comenzi_delivery_type', 'tipuri_livrare', ['delivery_type_id'], ['id']),
        ('fk_comenzi_payment_method', 'modalitati_de_plata', ['payment_method_id'], ['id'])
    ]
    
    # Add missing foreign keys
    for fk_name, ref_table, local_cols, remote_cols in foreign_keys_to_add:
        if fk_name not in existing_fks:
            op.create_foreign_key(
                fk_name, 'comenzi', ref_table,
                local_cols, remote_cols,
                ondelete='RESTRICT', onupdate='CASCADE'
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
    
    # Note: We don't drop the comenzi table in downgrade because it might have been
    # created by this migration or might have existed before. This is safer.
