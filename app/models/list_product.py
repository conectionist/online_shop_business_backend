from sqlalchemy import Column, Integer, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.core.database import Base


class ListProduct(Base):
    """SQLAlchemy model for liste_au_produse (list-product many-to-many relationship) table"""
    
    __tablename__ = "liste_au_produse"
    
    liste_id = Column(Integer, ForeignKey("liste.id"), primary_key=True)
    produse_id = Column(Integer, ForeignKey("produse.id"), primary_key=True)
    
    # Relationships
    list = relationship("List", foreign_keys=[liste_id], back_populates="products")
    product = relationship("Product", foreign_keys=[produse_id])
    
    # Indexes for foreign keys
    __table_args__ = (
        Index("fk_liste_has_produse_produse1_idx", "produse_id"),
        Index("fk_liste_has_produse_liste1_idx", "liste_id"),
        {"mysql_engine": "InnoDB"},
    ) 