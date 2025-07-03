from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Unitati(Base):
    """SQLAlchemy model for unitati (units) table"""
    
    __tablename__ = "unitati"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    denumire = Column(String(45), unique=True, nullable=False)
    
    # Define relationships if needed in the future
    # Example: products = relationship("Product", back_populates="unit")
