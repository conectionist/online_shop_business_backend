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

    __table_args__ = (
        Index("idx_refresh_tokens_admin_id", "admin_id"),
        Index("idx_refresh_tokens_expires_at", "expires_at"),
        {
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_unicode_ci",
        },
    )
