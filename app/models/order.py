from sqlalchemy import Column, Integer, String, TIMESTAMP, DateTime, ForeignKey, Index, text
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import relationship

from app.core.database import Base


class Order(Base):
    """SQLAlchemy model for comenzi (orders) table
    
    New fields added for delivery and payment method support:
    - delivery_type_id: Reference to delivery type (required)
    - payment_method_id: Reference to payment method (required)  
    - delivery_address: Optional address for home delivery
    """

    __tablename__ = "comenzi"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nume_client = Column(String(50), nullable=False)
    data_plasarii = Column(DateTime, nullable=False)
    liste_id = Column(Integer, ForeignKey("liste.id"), nullable=False)
    delivery_type_id = Column(TINYINT, ForeignKey("tipuri_livrare.id"), nullable=False)
    payment_method_id = Column(Integer, ForeignKey("modalitati_de_plata.id"), nullable=False)
    delivery_address = Column(String(150), nullable=True)
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
    delivery_type = relationship("DeliveryType", foreign_keys=[delivery_type_id])
    payment_method = relationship("ModalitatiPlata", foreign_keys=[payment_method_id])
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    __table_args__ = (
        Index("fk_comenzi_liste1_idx", "liste_id"),
        Index("idx_comenzi_data_plasarii", "data_plasarii"),
        Index("idx_comenzi_nume_client", "nume_client"),
        Index("idx_comenzi_delivery_type", "delivery_type_id"),
        Index("idx_comenzi_payment_method", "payment_method_id"),
        Index("idx_comenzi_delivery_address", "delivery_address"),
        {"mysql_engine": "InnoDB"},
    )


