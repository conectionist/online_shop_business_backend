"""Enhance refresh_tokens table for session management

Revision ID: 021
Revises: 020
Create Date: 2026-02-07 12:50:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "021"
down_revision = "020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns for enhanced session tracking
    op.add_column('refresh_tokens', 
        sa.Column('session_name', sa.String(length=100), nullable=True))
    op.add_column('refresh_tokens', 
        sa.Column('device_type', sa.String(length=50), nullable=True))
    op.add_column('refresh_tokens', 
        sa.Column('browser_name', sa.String(length=50), nullable=True))
    op.add_column('refresh_tokens', 
        sa.Column('os_name', sa.String(length=50), nullable=True))
    op.add_column('refresh_tokens', 
        sa.Column('location_city', sa.String(length=100), nullable=True))
    op.add_column('refresh_tokens', 
        sa.Column('location_country', sa.String(length=2), nullable=True))
    
    # Add composite index for efficient session queries
    op.create_index('idx_refresh_tokens_admin_active', 'refresh_tokens', 
                    ['admin_id', 'revoked_at', 'expires_at'])


def downgrade() -> None:
    op.drop_index('idx_refresh_tokens_admin_active', table_name='refresh_tokens')
    op.drop_column('refresh_tokens', 'location_country')
    op.drop_column('refresh_tokens', 'location_city')
    op.drop_column('refresh_tokens', 'os_name')
    op.drop_column('refresh_tokens', 'browser_name')
    op.drop_column('refresh_tokens', 'device_type')
    op.drop_column('refresh_tokens', 'session_name')
