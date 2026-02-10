"""Add refresh_tokens table for session management

Revision ID: 020
Revises: 019
Create Date: 2026-02-09 18:40:00.000000

This migration creates the refresh_tokens table with full session tracking
capabilities including device metadata, location tracking, and token rotation.

Consolidated from previously separate migrations for cleaner history.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision = "020"
down_revision = "019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create refresh_tokens table with all session management features."""

    # Fix admins.id type: schema.sql defines it as TINYINT but the SQLAlchemy
    # model uses Integer.  Align the DB column to Integer so the foreign key
    # on refresh_tokens.admin_id is compatible.  This is safe even if the
    # column is already INT (MySQL treats it as a no-op rebuild).
    op.alter_column(
        "admins",
        "id",
        existing_type=mysql.TINYINT(),
        type_=sa.Integer(),
        existing_nullable=False,
        autoincrement=True,
    )

    op.create_table(
        "refresh_tokens",
        # Primary key and foreign key
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("admin_id", sa.Integer(), sa.ForeignKey("admins.id"), nullable=False),

        # Token data
        sa.Column("token_hash", sa.String(length=64), nullable=False, unique=True),

        # Timestamps
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("last_used_at", sa.TIMESTAMP(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),

        # Revocation and rotation tracking
        sa.Column("revoked_at", sa.TIMESTAMP(), nullable=True),
        sa.Column("replaced_by_token_id", sa.Integer(), sa.ForeignKey("refresh_tokens.id"), nullable=True),

        # Request metadata
        sa.Column("ip_address", sa.String(length=45), nullable=True, comment="IPv4 or IPv6 address"),
        sa.Column("user_agent", sa.String(length=512), nullable=True),

        # Session identification and device metadata
        sa.Column("session_name", sa.String(length=100), nullable=True, comment="Human-readable session name"),
        sa.Column("device_type", sa.String(length=50), nullable=True, comment="desktop/mobile/tablet/unknown"),
        sa.Column("browser_name", sa.String(length=50), nullable=True, comment="Chrome/Firefox/Safari/etc"),
        sa.Column("os_name", sa.String(length=50), nullable=True, comment="Windows/macOS/Linux/iOS/Android"),

        # Location tracking (optional)
        sa.Column("location_city", sa.String(length=100), nullable=True),
        sa.Column("location_country", sa.String(length=2), nullable=True, comment="ISO 3166-1 alpha-2 country code"),

        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
    )

    # Create indexes for efficient queries
    # Note: Comments are for documentation only; SQL index comments are not supported by SQLAlchemy

    # Index for looking up tokens by admin (fast lookup of all sessions for an admin)
    op.create_index(
        "idx_refresh_tokens_admin_id",
        "refresh_tokens",
        ["admin_id"]
    )

    # Index for finding expired tokens (efficient cleanup of expired tokens)
    op.create_index(
        "idx_refresh_tokens_expires_at",
        "refresh_tokens",
        ["expires_at"]
    )

    # Unique index for token hash lookups (fast and unique token verification)
    op.create_index(
        "ix_refresh_tokens_token_hash",
        "refresh_tokens",
        ["token_hash"],
        unique=True
    )

    # Composite index for finding active sessions (optimized query for active sessions: non-revoked, non-expired)
    op.create_index(
        "idx_refresh_tokens_admin_active",
        "refresh_tokens",
        ["admin_id", "revoked_at", "expires_at"]
    )


def downgrade() -> None:
    """Drop refresh_tokens table and all indexes."""
    # Drop indexes first
    op.drop_index("idx_refresh_tokens_admin_active", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_token_hash", table_name="refresh_tokens")
    op.drop_index("idx_refresh_tokens_expires_at", table_name="refresh_tokens")
    op.drop_index("idx_refresh_tokens_admin_id", table_name="refresh_tokens")

    # Drop table
    op.drop_table("refresh_tokens")
