"""Cleanup category soft deletion (idempotent)

Revision ID: 018
Revises: 017
Create Date: 2025-01-09 01:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = "018"
down_revision = "017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Idempotent cleanup for migration 017 that may have failed.
    This migration is safe to run even if 017 completed successfully.
    """
    connection = op.get_bind()
    
    # Check if is_deleted column still exists
    result = connection.execute(text("""
        SELECT COUNT(*) FROM information_schema.COLUMNS 
        WHERE TABLE_SCHEMA = DATABASE() 
        AND TABLE_NAME = 'category' 
        AND COLUMN_NAME = 'is_deleted'
    """))
    column_exists = result.scalar() > 0
    
    if column_exists:
        # Column still exists, migration 017 failed - do the cleanup
        print("INFO: is_deleted column found, performing cleanup...")
        
        # 1) Delete foreign key references to soft-deleted categories
        # Delete from liste_au_categorii (list-category associations)
        op.execute(text("""
            DELETE lac FROM liste_au_categorii lac
            INNER JOIN category c ON lac.category_id = c.id
            WHERE c.is_deleted = 1
        """))
        
        # Delete from liste_au_produse_ordered (list-product ordering)
        op.execute(text("""
            DELETE lpo FROM liste_au_produse_ordered lpo
            INNER JOIN category c ON lpo.category_id = c.id
            WHERE c.is_deleted = 1
        """))
        
        # Move products from soft-deleted categories to "Uncategorized" (category_id = 1)
        op.execute(text("""
            UPDATE produse p
            INNER JOIN category c ON p.category_id = c.id
            SET p.category_id = 1
            WHERE c.is_deleted = 1
        """))
        
        # 2) Delete all soft-deleted categories
        op.execute(text("DELETE FROM category WHERE is_deleted = 1"))
        
        # 3) Compact order_index to sequential 1-N for remaining categories
        # First, temporarily negate all order_index values to avoid unique constraint violations
        op.execute(text("UPDATE category SET order_index = -order_index"))
        
        # Then assign new sequential values
        op.execute(text("SET @i := 0"))
        op.execute(
            text(
                """
                UPDATE category t
                JOIN (
                  SELECT id FROM category ORDER BY -order_index ASC, name ASC
                ) x ON x.id = t.id
                SET t.order_index = (@i := @i + 1)
                """
            )
        )
        
        # 4) Drop the index on is_deleted (if it exists)
        try:
            op.drop_index("idx_category_is_deleted", table_name="category")
        except Exception:
            # Index might not exist, that's okay
            pass
        
        # 5) Drop the is_deleted column
        op.drop_column("category", "is_deleted")
        
        print("INFO: Cleanup completed successfully")
    else:
        print("INFO: is_deleted column not found, migration 017 already completed successfully")


def downgrade() -> None:
    """
    No downgrade - this is a cleanup migration that should not be reversed.
    If you need to rollback, manually restore from backup.
    """
    pass
