"""
Change liste.expiration_date to DATETIME(6)

Revision ID: 011
Revises: 010
Create Date: 2025-09-26 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Alter column from DATE to DATETIME(6), keep it nullable
    op.alter_column(
        "liste",
        "expiration_date",
        existing_type=sa.Date(),
        type_=mysql.DATETIME(fsp=6),
        existing_nullable=True,
        nullable=True,
    )


def downgrade() -> None:
    # Revert back to DATE
    op.alter_column(
        "liste",
        "expiration_date",
        existing_type=mysql.DATETIME(fsp=6),
        type_=sa.Date(),
        existing_nullable=True,
        nullable=True,
    )


