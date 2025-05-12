from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi import HTTPException
from starlette import status

from models.tables import Product, Ordered_product, Order
from models.schemas import ProductCreate
from utils import delete_object


class ProductRepository:
    async def get_by_id(
            self,
            product_id: int,
            session: AsyncSession
    ):
        result = await session.execute(select(Product).where(Product.id == product_id))
        return result.scalars().first()

    async def get_by_name(
            self,
            product_name: str,
            session: AsyncSession
    ):
        result = await session.execute(select(Product).where(Product.name == product_name))
        return result.scalars().first()

    async def get_all(
            self,
            session: AsyncSession
    ):
        result = await session.execute(select(Product))
        return result.scalars().all()

    async def create(
            self,
            product: ProductCreate,
            session: AsyncSession
    ):
        try:
            new_product = Product(**product.model_dump())
            session.add(new_product)
            await session.commit()
            await session.refresh(new_product)
            return new_product

        except IntegrityError:
            await session.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Товар с ID: {product.id} уже сущетсвует")

    async def delete_product_by_id(
            self,
            product_id: int,
            session: AsyncSession
    ):
        search_prod_in_ordered_prods = await session.execute(select(Ordered_product).where(Ordered_product.product_id == product_id))
        orders = search_prod_in_ordered_prods.scalars().all()

        if orders:
            orders_id_massive = [order.order_id for order in orders]
            InOrdersException = HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                              detail=f"Товар с ID: {product_id} находится в заказах: {orders_id_massive}. Удаление невозможно.")
            raise InOrdersException

        return await delete_object(session, Product, product_id, "id")