"""
Increase business_details.list_not_available_msg length to 1000

Revision ID: 009
Revises: 008
Create Date: 2025-09-23 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "business_details",
        "list_not_available_msg",
        existing_type=sa.String(length=200),
        type_=sa.String(length=1000),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "business_details",
        "list_not_available_msg",
        existing_type=sa.String(length=1000),
        type_=sa.String(length=200),
        existing_nullable=True,
    )


