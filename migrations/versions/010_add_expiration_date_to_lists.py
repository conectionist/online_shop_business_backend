"""
Add expiration_date column to liste table

Revision ID: 010
Revises: 009
Create Date: 2025-01-27 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add expiration_date column to liste table
    op.add_column(
        "liste",
        sa.Column("expiration_date", sa.Date(), nullable=True)
    )
    
    # Add index for expiration_date for performance
    op.create_index(
        "idx_liste_expiration_date",
        "liste",
        ["expiration_date"]
    )


def downgrade() -> None:
    # Drop the index first
    op.drop_index("idx_liste_expiration_date", table_name="liste")
    
    # Drop the expiration_date column
    op.drop_column("liste", "expiration_date")
