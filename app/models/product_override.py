from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, Index, Enum, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import ENUM

from app.core.database import Base


class ProductOverride(Base):
    """SQLAlchemy model for product_overrides table"""
    
    __tablename__ = "product_overrides"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    produse_id = Column(Integer, ForeignKey("produse.id"), nullable=False)
    field_name = Column(ENUM('price', 'description', 'availability'), nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=False)
    notes = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default="CURRENT_TIMESTAMP")
    updated_at = Column(TIMESTAMP, nullable=False, server_default="CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
    
    # Relationships
    product = relationship("Product", foreign_keys=[produse_id])
    
    # Indexes for foreign keys and common queries
    __table_args__ = (
        Index("idx_product_active_override", "produse_id", "field_name", "is_active"),
        Index("fk_product_overrides_produse1_idx", "produse_id"),
        {"mysql_engine": "InnoDB"},
    ) 