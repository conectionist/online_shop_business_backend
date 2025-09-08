"""Ensure 'Uncategorized' category exists

Revision ID: 005
Revises: 004
Create Date: 2025-09-08 00:10:00.000000

"""
from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()

    # Insert 'Uncategorized' if missing
    connection.execute(text(
        """
        INSERT INTO category (name, is_deleted)
        SELECT :name, 0
        WHERE NOT EXISTS (
            SELECT 1 FROM category WHERE name = :name
        )
        """
    ), {"name": "Uncategorized"})


def downgrade():
    connection = op.get_bind()

    # Only delete if no products reference it and it's not used in list ordering
    connection.execute(text(
        """
        DELETE c FROM category c
        LEFT JOIN produse p ON p.category_id = c.id
        LEFT JOIN liste_au_categorii lc ON lc.category_id = c.id
        WHERE c.name = :name AND p.id IS NULL AND lc.category_id IS NULL
        """
    ), {"name": "Uncategorized"})
