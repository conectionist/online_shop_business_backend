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
    
    # Table arguments for constraints
    __table_args__ = (
        {"mysql_engine": "InnoDB"},
    )
