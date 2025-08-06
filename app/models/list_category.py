from sqlalchemy import Column, Integer, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.core.database import Base


class ListCategory(Base):
    """SQLAlchemy model for liste_au_categorii (list-category ordering) table"""
    
    __tablename__ = "liste_au_categorii"
    
    liste_id = Column(Integer, ForeignKey("liste.id"), primary_key=True)
    category_id = Column(Integer, ForeignKey("category.id"), primary_key=True)
    position = Column(Integer, nullable=False)
    
    # Relationships
    list = relationship("List", foreign_keys=[liste_id], back_populates="categories")
    category = relationship("Category", foreign_keys=[category_id])
    
    # Indexes for foreign keys and ordering
    __table_args__ = (
        Index("idx_liste_categorii_position", "liste_id", "position"),
        Index("fk_liste_au_categorii_liste1_idx", "liste_id"),
        Index("fk_liste_au_categorii_category1_idx", "category_id"),
        {"mysql_engine": "InnoDB"},
    ) 