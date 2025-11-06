"""Add payment_types table

Revision ID: 014
Revises: 013
Create Date: 2025-11-06 18:40

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '014'
down_revision = '013'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create payment_types table with explicit IDs (no auto-increment)
    op.create_table(
        'payment_types',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('friendly_name', sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
    )
    op.create_index('ix_payment_types_name', 'payment_types', ['name'], unique=True)

    # Seed payment types with explicit IDs
    conn = op.get_bind()
    conn.execute(sa.text(
        """
        INSERT INTO payment_types (id, name, friendly_name)
        VALUES 
            (0, 'custom', 'Nespecificat'),
            (1, 'cash', 'Numerar'),
            (2, 'physical_card', 'Plata cu cardul'),
            (3, 'online_card', 'Plata cu card online'),
            (4, 'revolut', 'Transfer Revolut'),
            (5, 'bank_transfer', 'Transfer bancar')
        ON DUPLICATE KEY UPDATE name = VALUES(name), friendly_name = VALUES(friendly_name)
        """
    ))


def downgrade() -> None:
    op.drop_index('ix_payment_types_name', table_name='payment_types')
    op.drop_table('payment_types')

