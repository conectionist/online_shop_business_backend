"""Remove soft deletion from categories

Revision ID: 017
Revises: 016
Create Date: 2025-01-09 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "017"
down_revision = "016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) Delete foreign key references to soft-deleted categories
    # Delete from liste_au_categorii (list-category associations)
    op.execute(sa.text("""
        DELETE lac FROM liste_au_categorii lac
        INNER JOIN category c ON lac.category_id = c.id
        WHERE c.is_deleted = 1
    """))
    
    # Delete from liste_au_produse_ordered (list-product ordering)
    op.execute(sa.text("""
        DELETE lpo FROM liste_au_produse_ordered lpo
        INNER JOIN category c ON lpo.category_id = c.id
        WHERE c.is_deleted = 1
    """))
    
    # Move products from soft-deleted categories to "Uncategorized" (category_id = 1)
    op.execute(sa.text("""
        UPDATE produse p
        INNER JOIN category c ON p.category_id = c.id
        SET p.category_id = 1
        WHERE c.is_deleted = 1
    """))
    
    # 2) Delete all soft-deleted categories (they're already hidden from users)
    op.execute(sa.text("DELETE FROM category WHERE is_deleted = 1"))
    
    # 3) Compact order_index to sequential 1-N for remaining categories
    # First, temporarily negate all order_index values to avoid unique constraint violations
    op.execute(sa.text("UPDATE category SET order_index = -order_index"))
    
    # Then assign new sequential values
    op.execute(sa.text("SET @i := 0"))
    op.execute(
        sa.text(
            """
            UPDATE category t
            JOIN (
              SELECT id FROM category ORDER BY -order_index ASC, name ASC
            ) x ON x.id = t.id
            SET t.order_index = (@i := @i + 1)
            """
        )
    )
    
    # 4) Drop the index on is_deleted
    op.drop_index("idx_category_is_deleted", table_name="category")
    
    # 5) Drop the is_deleted column
    op.drop_column("category", "is_deleted")


def downgrade() -> None:
    # Add back is_deleted column with default False
    op.add_column(
        "category",
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("0"))
    )
    
    # Recreate the index
    op.create_index("idx_category_is_deleted", "category", ["is_deleted"])
