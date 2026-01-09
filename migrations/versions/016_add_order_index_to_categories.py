"""Add order_index to category

Revision ID: 016
Revises: 015
Create Date: 2025-01-XX 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision = "016"
down_revision = "015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) Add new column as nullable to avoid failing on existing rows
    op.add_column(
        "category",
        sa.Column("order_index", mysql.TINYINT(), nullable=True),
    )

    # 2) Backfill order_index by current id order (dense sequence starting at 1)
    # Use MySQL user variables for row numbering
    op.execute(sa.text("SET @i := 0"))
    op.execute(
        sa.text(
            """
            UPDATE category t
            JOIN (
              SELECT id FROM category ORDER BY id ASC
            ) x ON x.id = t.id
            SET t.order_index = (@i := @i + 1)
            """
        )
    )

    # 3) Enforce NOT NULL and add unique constraint on order_index
    op.alter_column("category", "order_index", existing_type=mysql.TINYINT(), nullable=False)
    op.create_unique_constraint(
        "uq_category_order_index",
        "category",
        ["order_index"],
    )


def downgrade() -> None:
    # Drop unique constraint and column in reverse order
    op.drop_constraint("uq_category_order_index", "category", type_="unique")
    op.drop_column("category", "order_index")
