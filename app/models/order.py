from sqlalchemy import Column, Integer, String, TIMESTAMP, DateTime, ForeignKey, Index, text
from sqlalchemy.orm import relationship

from app.core.database import Base


class Order(Base):
    """SQLAlchemy model for comenzi (orders) table"""

    __tablename__ = "comenzi"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nume_client = Column(String(50), nullable=False)
    data_plasarii = Column(DateTime, nullable=False)
    liste_id = Column(Integer, ForeignKey("liste.id"), nullable=False)
    order_notes = Column(String(500), nullable=True)
    created_at = Column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at = Column(
        TIMESTAMP,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
    )

    # Relationships
    list = relationship("List", foreign_keys=[liste_id])
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    __table_args__ = (
        Index("fk_comenzi_liste1_idx", "liste_id"),
        Index("idx_comenzi_data_plasarii", "data_plasarii"),
        Index("idx_comenzi_nume_client", "nume_client"),
        {"mysql_engine": "InnoDB"},
    )


