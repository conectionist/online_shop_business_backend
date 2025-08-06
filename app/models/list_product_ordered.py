from sqlalchemy import Column, Integer, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.core.database import Base


class ListProductOrdered(Base):
    """SQLAlchemy model for liste_au_produse_ordered (list-product ordering within categories) table"""
    
    __tablename__ = "liste_au_produse_ordered"
    
    liste_id = Column(Integer, ForeignKey("liste.id"), primary_key=True)
    produse_id = Column(Integer, ForeignKey("produse.id"), primary_key=True)
    category_id = Column(Integer, ForeignKey("category.id"), nullable=False)
    position = Column(Integer, nullable=False)
    stoc_produs = Column(Integer, nullable=True)
    
    # Relationships
    list = relationship("List", foreign_keys=[liste_id], back_populates="products_ordered")
    product = relationship("Product", foreign_keys=[produse_id])
    category = relationship("Category", foreign_keys=[category_id])
    
    # Indexes for foreign keys and ordering
    __table_args__ = (
        Index("idx_liste_produse_category_position", "liste_id", "category_id", "position"),
        Index("fk_liste_au_produse_ordered_liste1_idx", "liste_id"),
        Index("fk_liste_au_produse_ordered_produse1_idx", "produse_id"),
        Index("fk_liste_au_produse_ordered_category1_idx", "category_id"),
        {"mysql_engine": "InnoDB"},
    ) 