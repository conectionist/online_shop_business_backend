from sqlalchemy import Column, Integer, String, SmallInteger, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.core.database import Base


class ProductImage(Base):
    """SQLAlchemy model for product_images table"""
    
    __tablename__ = "product_images"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    path = Column(String(256), nullable=False)
    produse_id = Column(Integer, ForeignKey("produse.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    position = Column(SmallInteger, nullable=False, default=0)
    
    # Relationship back to product - defined here to avoid circular imports
    product = relationship("Product", back_populates="images")
    
    # Indexes for foreign keys and position
    __table_args__ = (
        Index("fk_product_images_produse1_idx", "produse_id"),
        Index("idx_product_images_position", "position"),
        {"mysql_engine": "InnoDB"},
    )
