from sqlalchemy import Column, Integer, ForeignKey, Index
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import relationship

from app.core.database import Base


class ListDeliveryType(Base):
    """SQLAlchemy model for liste_au_tipuri_livrare (list-delivery type many-to-many relationship) table"""
    
    __tablename__ = "liste_au_tipuri_livrare"
    
    liste_id = Column(Integer, ForeignKey("liste.id"), primary_key=True)
    tipuri_livrare_id = Column(TINYINT, ForeignKey("tipuri_livrare.id"), primary_key=True)
    
    # Relationships
    list = relationship("List", foreign_keys=[liste_id], back_populates="delivery_types")
    delivery_type = relationship("DeliveryType", foreign_keys=[tipuri_livrare_id])
    
    # Indexes for foreign keys
    __table_args__ = (
        Index("fk_liste_has_tipuri_livrare_tipuri_livrare1_idx", "tipuri_livrare_id"),
        Index("fk_liste_has_tipuri_livrare_liste1_idx", "liste_id"),
        {"mysql_engine": "InnoDB"},
    ) 