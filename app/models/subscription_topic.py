from sqlalchemy import Column, Integer, TIMESTAMP, text, ForeignKey, UniqueConstraint, Index

from app.core.database import Base


class SubscriptionTopic(Base):
    """Mapping between a web push subscription and a notification topic."""

    __tablename__ = "subscription_topics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    subscription_id = Column(
        Integer,
        ForeignKey("web_push_subscription.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    topic_id = Column(
        Integer,
        ForeignKey("notification_topics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at = Column(
        TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

    __table_args__ = (
        UniqueConstraint(
            "subscription_id",
            "topic_id",
            name="uq_subscription_topic",
        ),
        Index("idx_subscription_topics_subscription", "subscription_id"),
        Index("idx_subscription_topics_topic", "topic_id"),
        {
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_unicode_ci",
        },
    )


