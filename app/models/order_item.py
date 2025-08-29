from sqlalchemy import Column, Integer, SmallInteger, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.core.database import Base


class OrderItem(Base):
    """SQLAlchemy model for comenzi_au_produse (order items) table

    Composite primary key: (comenzi_id, produse_id)
    """

    __tablename__ = "comenzi_au_produse"

    comenzi_id = Column(Integer, ForeignKey("comenzi.id"), primary_key=True, nullable=False)
    produse_id = Column(Integer, ForeignKey("produse.id"), primary_key=True, nullable=False)
    pret_produs = Column(SmallInteger, nullable=False)
    cantitate_produs = Column(SmallInteger, nullable=False)
    unitati_id = Column(Integer, ForeignKey("unitati.id"), nullable=False)

    # Relationships
    order = relationship("Order", foreign_keys=[comenzi_id])
    product = relationship("Product", foreign_keys=[produse_id])
    unit = relationship("Unitati", foreign_keys=[unitati_id])

    __table_args__ = (
        Index("fk_comenzi_has_produse_produse1_idx", "produse_id"),
        Index("fk_comenzi_has_produse_comenzi1_idx", "comenzi_id"),
        Index("fk_comenzi_has_produse_unitati1_idx", "unitati_id"),
        {"mysql_engine": "InnoDB"},
    )


