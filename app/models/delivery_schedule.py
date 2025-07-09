from sqlalchemy import Column, String, Integer, UniqueConstraint
from app.core.database import Base


class DeliverySchedule(Base):
    """SQLAlchemy model for delivery schedules (orare_livrari)."""
    
    __tablename__ = "orare_livrari"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    orar_livrari = Column(String(1000), nullable=False)
    
    # Table constraints
    __table_args__ = (
        UniqueConstraint('id', name='id_UNIQUE'),
    )
