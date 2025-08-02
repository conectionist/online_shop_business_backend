"""Admin model for authentication"""

from sqlalchemy import Column, Integer, String
from app.core.database import Base


class Admin(Base):
    """Admin user model for authentication"""

    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)

    def __repr__(self):
        return f"<Admin(id={self.id}, username='{self.username}')>" 