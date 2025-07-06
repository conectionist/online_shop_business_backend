from sqlalchemy import Column, Integer, String

from app.core.database import Base


class ModalitatiPlata(Base):
    """SQLAlchemy model for modalitati_de_plata (payment methods) table"""
    
    __tablename__ = "modalitati_de_plata"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    denumire = Column(String(45), unique=True, nullable=False)
