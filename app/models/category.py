from sqlalchemy import Column, Integer, String, TIMESTAMP, Boolean, text, Index
from sqlalchemy.dialects.mysql import TINYINT
from app.core.database import Base


class Category(Base):
    """SQLAlchemy model for category table"""
    
    __tablename__ = "category"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(200), nullable=False, unique=True)
    image_path = Column(String(256), nullable=True)
    order_index = Column(TINYINT, nullable=False, unique=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
    is_deleted = Column(Boolean, nullable=False, default=False, server_default=text("0"))
    
    # Index for soft delete functionality
    __table_args__ = (
        Index("idx_category_is_deleted", "is_deleted"),
        Index("name_UNIQUE", "name", unique=True),
        {"mysql_engine": "InnoDB"},
    )
