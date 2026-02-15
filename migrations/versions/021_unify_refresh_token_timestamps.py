"""Unify refresh_tokens.expires_at column type from DateTime to TIMESTAMP

Revision ID: 021
Revises: 020
Create Date: 2026-02-15 12:00:00.000000

All other timestamp columns in refresh_tokens (created_at, last_used_at,
revoked_at) already use TIMESTAMP.  This migration aligns expires_at to
the same type for consistent timezone handling in MySQL.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "021"
down_revision = "020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "refresh_tokens",
        "expires_at",
        existing_type=sa.DateTime(),
        type_=sa.TIMESTAMP(),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "refresh_tokens",
        "expires_at",
        existing_type=sa.TIMESTAMP(),
        type_=sa.DateTime(),
        existing_nullable=False,
    )
