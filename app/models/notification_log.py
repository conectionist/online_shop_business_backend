from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, text, UniqueConstraint, Index
from app.core.database import Base


class NotificationLog(Base):
    __tablename__ = "notification_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    subscription_id = Column(Integer, ForeignKey("web_push_subscription.id", ondelete="CASCADE"), nullable=False, index=True)
    event_key = Column(String(128), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    __table_args__ = (
        UniqueConstraint("subscription_id", "event_key", name="uq_notification_event_per_subscription"),
        Index("idx_notification_subscription", "subscription_id"),
        {
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_unicode_ci",
        },
    )
