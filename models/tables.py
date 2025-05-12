from datetime import datetime
from sqlalchemy import String, Integer, func, PrimaryKeyConstraint, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.mysql import DECIMAL
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, relationship, mapped_column, DeclarativeBase


class Base(AsyncAttrs, DeclarativeBase):
    __abstract__ = True

class User(Base):
    __tablename__ = "users"

    phone: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String)
    last_name: Mapped[str] = mapped_column(String)
    patrynomic: Mapped[str] = mapped_column(String)


    # Связь покупатель->заказ один ко многим
    order = relationship("Order", back_populates="user", cascade="all, delete-orphan")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String)
    price: Mapped[float] = mapped_column(DECIMAL(10, 2))
    quantity: Mapped[int] = mapped_column(Integer)

    ordered_products = relationship("Ordered_product", back_populates="product", uselist=True)


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_phone: Mapped[str] = mapped_column(String, ForeignKey("users.phone"))
    customer_name: Mapped[str] = mapped_column(String)
    date: Mapped[datetime] = mapped_column(server_default=func.now())
    total: Mapped[float] = mapped_column(DECIMAL(10, 2))

    # Связь заказ->покупатель, многие ко одному
    user = relationship("User", back_populates="order")

    # Связь заказ->заказ-товар, один ко многим
    ordered_products = relationship("Ordered_product", back_populates="order", uselist=True,
                                    cascade="all, delete-orphan")


class Ordered_product(Base):
    __tablename__ = "ordered_products"

    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id"))
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"))
    chosen_quantity: Mapped[int] = mapped_column(Integer)

    __table_args__ = (
        PrimaryKeyConstraint("order_id", "product_id"),
        UniqueConstraint("order_id", "product_id"),  # Ограничение уникальности
    )
    # Связь заказ-товар->заказ, многие ко одному
    order = relationship("Order", back_populates="ordered_products")
    # Связь заказ-товар->товар многие к одному
    product = relationship("Product", back_populates="ordered_products")
