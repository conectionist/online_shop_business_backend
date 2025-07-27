from sqlalchemy import Column, Integer, String, TIMESTAMP, Boolean, text, SmallInteger, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.product_image import ProductImage


class Product(Base):
    """SQLAlchemy model for produse (products) table"""
    
    __tablename__ = "produse"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nume = Column(String(45), nullable=False, unique=True)
    cantitate = Column(SmallInteger, nullable=False)
    pret = Column(SmallInteger, nullable=False)
    description = Column(String(1500), nullable=True)
    category_id = Column(Integer, ForeignKey("category.id"), nullable=False)
    unitati_id = Column(Integer, ForeignKey("unitati.id"), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
    is_deleted = Column(Boolean, nullable=False, default=False, server_default=text("0"))
    
    # Relationships
    category = relationship("Category", foreign_keys=[category_id])
    unit = relationship("Unitati", foreign_keys=[unitati_id])
    images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan", order_by="ProductImage.position")
    
    # Indexes for foreign keys and soft delete functionality
    __table_args__ = (
        Index("fk_produse_category1_idx", "category_id"),
        Index("fk_produse_unitati1_idx", "unitati_id"),
        Index("idx_produse_is_deleted", "is_deleted"),
        {"mysql_engine": "InnoDB"},
    )
    
    @property
    def primary_image(self):
        """Return the primary image (position=0) or None if no images"""
        for image in self.images:
            if image.position == 0:
                return image
        return None if not self.images else self.images[0]
