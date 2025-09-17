"""
Add notification_log table for event-key dedupe

Revision ID: 008
Revises: 007
Create Date: 2025-09-17 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notification_log",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("subscription_id", sa.Integer(), nullable=False, index=True),
        sa.Column("event_key", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["subscription_id"], ["web_push_subscription.id"], ondelete="CASCADE"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )
    op.create_unique_constraint(
        "uq_notification_event_per_subscription",
        "notification_log",
        ["subscription_id", "event_key"],
    )
    op.create_index("idx_notification_subscription", "notification_log", ["subscription_id"]) 


def downgrade() -> None:
    op.drop_index("idx_notification_subscription", table_name="notification_log")
    op.drop_constraint("uq_notification_event_per_subscription", "notification_log", type_="unique")
    op.drop_table("notification_log")
