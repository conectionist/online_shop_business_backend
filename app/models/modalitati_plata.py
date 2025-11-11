from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import relationship

from app.core.database import Base


class ModalitatiPlata(Base):
    """SQLAlchemy model for modalitati_de_plata (payment methods) table"""
    
    __tablename__ = "modalitati_de_plata"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(20), unique=True, nullable=False)
    description = Column(String(100), nullable=False)
    payment_type_id = Column(Integer, ForeignKey("payment_types.id"), nullable=False)
    required_data = Column(JSON, nullable=True)
    
    # Relationships
    payment_type = relationship("PaymentType", foreign_keys=[payment_type_id])
