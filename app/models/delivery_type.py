from sqlalchemy import Column, String, UniqueConstraint
from sqlalchemy.dialects.mysql import TINYINT
from app.core.database import Base


class DeliveryType(Base):
    """SQLAlchemy model for delivery types (tipuri_livrare)."""
    
    __tablename__ = "tipuri_livrare"
    
    id = Column(TINYINT, primary_key=True, index=True, autoincrement=True)
    denumire = Column(String(45), nullable=False, unique=True)
    
    __table_args__ = (
        UniqueConstraint('denumire', name='denumire_UNIQUE'),
    )
