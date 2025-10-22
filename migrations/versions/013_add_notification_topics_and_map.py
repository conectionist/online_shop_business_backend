"""add notification topics and subscription mapping

Revision ID: 013
Revises: 012
Create Date: 2025-10-22 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '013'
down_revision = '012'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'notification_topics',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
    )
    op.create_index('ix_notification_topics_name', 'notification_topics', ['name'], unique=True)

    op.create_table(
        'subscription_topics',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('subscription_id', sa.Integer(), sa.ForeignKey('web_push_subscription.id', ondelete='CASCADE'), nullable=False),
        sa.Column('topic_id', sa.Integer(), sa.ForeignKey('notification_topics.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('subscription_id', 'topic_id', name='uq_subscription_topic'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
    )
    op.create_index('idx_subscription_topics_subscription', 'subscription_topics', ['subscription_id'], unique=False)
    op.create_index('idx_subscription_topics_topic', 'subscription_topics', ['topic_id'], unique=False)

    # Seed default topics
    conn = op.get_bind()
    conn.execute(sa.text(
        """
        INSERT INTO notification_topics (name, description)
        VALUES 
            ('admin_login', 'Notify admins when an admin logs in'),
            ('new_order', 'Notify admins when a new order is placed'),
            ('list_published', 'Notify apps when a new list is published')
        ON DUPLICATE KEY UPDATE name = VALUES(name)
        """
    ))


def downgrade() -> None:
    op.drop_index('idx_subscription_topics_topic', table_name='subscription_topics')
    op.drop_index('idx_subscription_topics_subscription', table_name='subscription_topics')
    op.drop_table('subscription_topics')

    op.drop_index('ix_notification_topics_name', table_name='notification_topics')
    op.drop_table('notification_topics')


