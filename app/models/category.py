from sqlalchemy import Column, Integer, String, TIMESTAMP, text, Index
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
    
    __table_args__ = (
        Index("name_UNIQUE", "name", unique=True),
        {"mysql_engine": "InnoDB"},
    )
