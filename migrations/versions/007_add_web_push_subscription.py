"""
Add web_push_subscription table

Revision ID: 007
Revises: 006
Create Date: 2025-09-17 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "web_push_subscription",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=True, index=True),
        sa.Column("endpoint", sa.String(length=512), nullable=False),
        sa.Column("p256dh_key", sa.String(length=255), nullable=False),
        sa.Column("auth_key", sa.String(length=255), nullable=False),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("last_success_at", sa.TIMESTAMP(), nullable=True),
        sa.Column("last_failure_reason", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
        ),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )

    # Unique constraint for endpoint
    op.create_unique_constraint(
        "uq_webpush_endpoint", "web_push_subscription", ["endpoint"]
    )

    # Indexes
    op.create_index("idx_webpush_user_id", "web_push_subscription", ["user_id"]) 
    op.create_index("idx_webpush_is_active", "web_push_subscription", ["is_active"]) 


def downgrade() -> None:
    op.drop_index("idx_webpush_is_active", table_name="web_push_subscription")
    op.drop_index("idx_webpush_user_id", table_name="web_push_subscription")
    op.drop_constraint("uq_webpush_endpoint", "web_push_subscription", type_="unique")
    op.drop_table("web_push_subscription")
