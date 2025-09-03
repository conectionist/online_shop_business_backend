from sqlalchemy import Column, Integer, String, SmallInteger
from app.core.database import Base


class BusinessDetails(Base):
    """SQLAlchemy model for business_details table."""
    
    __tablename__ = "business_details"
    
    id = Column(SmallInteger, primary_key=True, autoincrement=True)
    adresa = Column(String(200), nullable=True)
    telefon = Column(String(20), nullable=True)
    logo_path = Column(String(256), nullable=True)
    motto = Column(String(256), nullable=True)
    list_not_available_msg = Column(String(200), nullable=True)
    alte_detalii = Column(String(500), nullable=True)
    delivery_tax = Column(SmallInteger, nullable=True, server_default="0")
    # Optional merchant identity fields
    business_name = Column(String(100), nullable=True)
    registration_number = Column(String(20), nullable=True)
    CUI = Column(String(16), nullable=True)
    email = Column(String(100), nullable=True)
    operating_hours = Column(String(150), nullable=True)
    representative = Column(String(100), nullable=True)
    
    # Table arguments for constraints
    __table_args__ = (
        {"mysql_engine": "InnoDB"},
    )
