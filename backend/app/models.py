"""
All database models in one file. Flat, no foreign keys.

SQLAlchemy 2.0 style with mapped_column.
"""
from sqlalchemy import JSON, Boolean, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # Shopify GID
    title: Mapped[str] = mapped_column(String, default="")
    handle: Mapped[str] = mapped_column(String, default="")
    status: Mapped[str] = mapped_column(String, default="active")
    vendor: Mapped[str | None] = mapped_column(String, nullable=True)
    product_type: Mapped[str | None] = mapped_column(String, nullable=True)
    price_min: Mapped[float] = mapped_column(Float, default=0.0)
    price_max: Mapped[float] = mapped_column(Float, default=0.0)
    variants: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    collections: Mapped[list | None] = mapped_column(JSON, nullable=True)
    featured_image_url: Mapped[str | None] = mapped_column(String, nullable=True)
    inventory_total: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[str | None] = mapped_column(String, nullable=True)
    updated_at: Mapped[str | None] = mapped_column(String, nullable=True)


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # Shopify GID
    order_number: Mapped[str] = mapped_column(String, default="")
    total_price: Mapped[float] = mapped_column(Float, default=0.0)
    subtotal_price: Mapped[float] = mapped_column(Float, default=0.0)
    total_discounts: Mapped[float] = mapped_column(Float, default=0.0)
    total_tax: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String, default="USD")
    financial_status: Mapped[str] = mapped_column(String, default="pending")
    fulfillment_status: Mapped[str | None] = mapped_column(String, nullable=True)
    line_items: Mapped[list | None] = mapped_column(JSON, nullable=True)
    customer_id: Mapped[str | None] = mapped_column(String, nullable=True)
    customer_email: Mapped[str | None] = mapped_column(String, nullable=True)
    customer_name: Mapped[str | None] = mapped_column(String, nullable=True)
    discount_codes: Mapped[list | None] = mapped_column(JSON, nullable=True)
    landing_site: Mapped[str | None] = mapped_column(String, nullable=True)
    referring_site: Mapped[str | None] = mapped_column(String, nullable=True)
    processed_at: Mapped[str] = mapped_column(String, default="")
    created_at: Mapped[str | None] = mapped_column(String, nullable=True)
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=False)


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # Shopify GID
    email: Mapped[str] = mapped_column(String, default="")
    first_name: Mapped[str] = mapped_column(String, default="")
    last_name: Mapped[str] = mapped_column(String, default="")
    orders_count: Mapped[int] = mapped_column(Integer, default=0)
    total_spent: Mapped[float] = mapped_column(Float, default=0.0)
    tags: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[str | None] = mapped_column(String, nullable=True)
    last_order_at: Mapped[str | None] = mapped_column(String, nullable=True)


class Event(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # uuid4 string
    event_type: Mapped[str] = mapped_column(String, default="")
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[str | None] = mapped_column(String, nullable=True)
