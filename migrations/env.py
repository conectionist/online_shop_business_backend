import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# Import your models here to ensure they're registered
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.list import List
from app.models.delivery_type import DeliveryType
from app.models.modalitati_plata import ModalitatiPlata
from app.models.payment_type import PaymentType
from app.models.category import Category
from app.models.unitati import Unitati
from app.models.business_details import BusinessDetails
from app.models.delivery_schedule import DeliverySchedule
from app.models.list_product import ListProduct
from app.models.list_category import ListCategory
from app.models.list_product_ordered import ListProductOrdered
from app.models.list_delivery_type import ListDeliveryType
from app.models.product_image import ProductImage
from app.models.product_override import ProductOverride
from app.models.admin import Admin

# Import the base class for metadata
from app.core.database import Base

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the database URL from environment variables
def get_url():
    return f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

# Override the sqlalchemy.url in alembic.ini
config.set_main_option("sqlalchemy.url", get_url())

# add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
