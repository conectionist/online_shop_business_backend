from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, TIMESTAMP, text, Index
from sqlalchemy.dialects import mysql

from app.core.database import Base


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    admin_id = Column(mysql.TINYINT(), ForeignKey("admins.id"), nullable=False, index=True)

    token_hash = Column(String(64), nullable=False, unique=True, index=True)

    created_at = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    last_used_at = Column(TIMESTAMP, nullable=True)

    expires_at = Column(DateTime, nullable=False, index=True)

    revoked_at = Column(TIMESTAMP, nullable=True)

    replaced_by_token_id = Column(Integer, ForeignKey("refresh_tokens.id"), nullable=True)

    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(512), nullable=True)

    # Enhanced session metadata
    session_name = Column(String(100), nullable=True)
    device_type = Column(String(50), nullable=True)  # desktop, mobile, tablet, unknown
    browser_name = Column(String(50), nullable=True)  # Chrome, Firefox, Safari, etc.
    os_name = Column(String(50), nullable=True)  # Windows, macOS, Linux, iOS, Android
    location_city = Column(String(100), nullable=True)
    location_country = Column(String(2), nullable=True)  # ISO country code

    __table_args__ = (
        Index("idx_refresh_tokens_admin_id", "admin_id"),
        Index("idx_refresh_tokens_expires_at", "expires_at"),
        Index("idx_refresh_tokens_admin_active", "admin_id", "revoked_at", "expires_at"),
        {
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_unicode_ci",
        },
    )
