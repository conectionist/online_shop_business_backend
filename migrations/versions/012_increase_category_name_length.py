"""
Increase category.name from VARCHAR(45) to VARCHAR(200)

Revision ID: 012
Revises: 011
Create Date: 2025-01-27 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "012"
down_revision = "011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Increase category name length from VARCHAR(45) to VARCHAR(200)
    op.alter_column(
        "category",
        "name",
        existing_type=mysql.VARCHAR(length=45),
        type_=mysql.VARCHAR(length=200),
        existing_nullable=False,
        nullable=False,
    )


def downgrade() -> None:
    # Revert back to VARCHAR(45)
    op.alter_column(
        "category",
        "name",
        existing_type=mysql.VARCHAR(length=200),
        type_=mysql.VARCHAR(length=45),
        existing_nullable=False,
        nullable=False,
    )
