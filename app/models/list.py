from sqlalchemy import Column, Integer, String, TIMESTAMP, Boolean, text, ForeignKey, Index, Date, SmallInteger
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.delivery_schedule import DeliverySchedule


class List(Base):
    """SQLAlchemy model for liste (lists) table"""
    
    __tablename__ = "liste"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    data = Column(Date, nullable=False)
    is_current = Column(SmallInteger, nullable=False)
    is_published = Column(SmallInteger, nullable=True)
    mesaj_introducere = Column(String(100), nullable=True)
    alte_detalii = Column(String(500), nullable=True)
    numar_whatsapp = Column(String(15), nullable=True)
    orare_livrari_id = Column(Integer, ForeignKey("orare_livrari.id"), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(TIMESTAMP, nullable=False, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
    is_deleted = Column(SmallInteger, nullable=False, default=0, server_default=text("0"))  # Added for soft deletion consistency
    
    # Relationships
    delivery_schedule = relationship("DeliverySchedule", foreign_keys=[orare_livrari_id])
    
    # Many-to-many relationships
    products = relationship("ListProduct", back_populates="list")
    delivery_types = relationship("ListDeliveryType", back_populates="list")
    
    # Indexes for foreign keys and soft delete functionality
    __table_args__ = (
        Index("fk_liste_orare_livrari1_idx", "orare_livrari_id"),
        Index("idx_liste_data", "data"),
        Index("idx_liste_is_deleted", "is_deleted"),  # Added for soft deletion consistency
        {"mysql_engine": "InnoDB"},
    )
