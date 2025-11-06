from sqlalchemy import Column, Integer, String

from app.core.database import Base


class PaymentType(Base):
    """SQLAlchemy model for payment_types table"""
    
    __tablename__ = "payment_types"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=False)
    name = Column(String(50), unique=True, nullable=False)
    friendly_name = Column(String(100), nullable=False)

