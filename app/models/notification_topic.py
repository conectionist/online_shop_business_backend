from sqlalchemy import Column, Integer, String, TIMESTAMP, text

from app.core.database import Base


class NotificationTopic(Base):
    """Notification topics that subscriptions can opt into.

    Examples: "admin_login", "new_order", "list_published".
    """

    __tablename__ = "notification_topics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)
    created_at = Column(
        TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

    __table_args__ = (
        {
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_unicode_ci",
        },
    )


