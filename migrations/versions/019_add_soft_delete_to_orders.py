"""Add soft delete to orders

Revision ID: 019
Revises: 018
Create Date: 2025-01-XX 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = "019"
down_revision = "018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add is_deleted column to comenzi table for soft delete functionality.
    """
    # Add is_deleted column (TINYINT to match lists pattern)
    op.add_column(
        "comenzi",
        sa.Column(
            "is_deleted",
            sa.SmallInteger(),
            nullable=False,
            server_default=text("0")
        )
    )
    
    # Set all existing orders to not deleted
    op.execute(text("UPDATE comenzi SET is_deleted = 0"))
    
    # Add index for query performance
    op.create_index(
        "idx_comenzi_is_deleted",
        "comenzi",
        ["is_deleted"]
    )


def downgrade() -> None:
    """
    Remove soft delete column and index from comenzi table.
    """
    # Drop index
    op.drop_index("idx_comenzi_is_deleted", table_name="comenzi")
    
    # Drop column
    op.drop_column("comenzi", "is_deleted")
