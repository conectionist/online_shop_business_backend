from sqlalchemy import Column, Integer, String, TIMESTAMP, Boolean, text, Index
from sqlalchemy.orm import declarative_mixin

from app.core.database import Base


class WebPushSubscription(Base):
    """Stores Web Push subscription endpoints and keys.

    Device-level for now; can be associated with users in future via nullable user_id.
    """

    __tablename__ = "web_push_subscription"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Nullable for now; reserved for future user mapping
    user_id = Column(Integer, nullable=True, index=True)

    # Web Push endpoint and keys
    endpoint = Column(String(512), nullable=False, unique=True)
    p256dh_key = Column(String(255), nullable=False)
    auth_key = Column(String(255), nullable=False)

    # Metadata
    user_agent = Column(String(512), nullable=True)
    is_active = Column(Boolean, nullable=False, server_default=text("1"))
    last_success_at = Column(TIMESTAMP, nullable=True)
    last_failure_reason = Column(String(512), nullable=True)

    created_at = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))

    __table_args__ = (
        Index("idx_webpush_user_id", "user_id"),
        Index("idx_webpush_is_active", "is_active"),
        {
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_unicode_ci",
        },
    )
