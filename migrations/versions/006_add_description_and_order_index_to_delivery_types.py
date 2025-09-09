"""
Add description and order_index to tipuri_livrare

Revision ID: 006
Revises: 005
Create Date: 2025-09-09 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) Add new columns as nullable to avoid failing on existing rows
    op.add_column(
        "tipuri_livrare",
        sa.Column("description", sa.String(length=150), nullable=True),
    )
    op.add_column(
        "tipuri_livrare",
        sa.Column("order_index", mysql.TINYINT(), nullable=True),
    )

    # 2) Backfill order_index by current id order (dense sequence starting at 1)
    # Use MySQL user variables for row numbering
    op.execute(sa.text("SET @i := 0"))
    op.execute(
        sa.text(
            """
            UPDATE tipuri_livrare t
            JOIN (
              SELECT id FROM tipuri_livrare ORDER BY id ASC
            ) x ON x.id = t.id
            SET t.order_index = (@i := @i + 1)
            """
        )
    )

    # 3) Enforce NOT NULL and add unique constraint on order_index
    op.alter_column("tipuri_livrare", "order_index", existing_type=mysql.TINYINT(), nullable=False)
    op.create_unique_constraint(
        "uq_tipuri_livrare_order_index",
        "tipuri_livrare",
        ["order_index"],
    )


def downgrade() -> None:
    # Drop unique constraint and columns in reverse order
    op.drop_constraint("uq_tipuri_livrare_order_index", "tipuri_livrare", type_="unique")
    op.drop_column("tipuri_livrare", "order_index")
    op.drop_column("tipuri_livrare", "description")


