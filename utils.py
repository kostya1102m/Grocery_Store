from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.responses import JSONResponse
from starlette.templating import Jinja2Templates

from database import async_session_maker
from models.tables import Product, User, Ordered_product


async def get_db() -> AsyncSession:
    async with async_session_maker() as session:
        yield session

templates = Jinja2Templates(directory="templates")
customer_templates = Jinja2Templates(directory="templates/customer")
manager_templates = Jinja2Templates(directory="templates/manager")


async def create_item(item_create_model, item_model, session: AsyncSession = Depends(get_db)):
    new_item = item_model(**item_create_model.dict())
    session.add(new_item)
    await session.commit()
    await session.refresh(new_item)
    return new_item


async def get_user_by_credentials(user_credentials, session: AsyncSession):
    query = select(User).where(User.phone == user_credentials.phone,
                               User.first_name == user_credentials.first_name,
                               User.last_name == user_credentials.last_name,
                               User.patrynomic == user_credentials.patrynomic)
    result = await session.execute(query)
    return result.scalars().first()

async def delete_object(session: AsyncSession, model, identifier, identifier_field):
        result = await session.execute(select(model).where(getattr(model, identifier_field) == identifier))
        obj = result.scalars().first()

        if obj is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{model.__name__} с ключом {identifier} не найден")

        await session.delete(obj)
        await session.commit()
        return obj


async def delete_product_by_id(session: AsyncSession, product_id):

    search_prod_in_ordered_prods = await session.execute(
        select(Ordered_product).where(Ordered_product.product_id == product_id))

    orders = search_prod_in_ordered_prods.scalars().all()
    if orders:
        orders_id_massive = [order.order_id for order in orders]
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Продукт с id {product_id} находится в заказах {orders_id_massive}. Удаление отказано.")

    await delete_object(session, Product, product_id, "id")
    return JSONResponse(status_code=status.HTTP_200_OK, content={
        'detail': f"Продукт с id {product_id} удален."
    })


async def get_items(item_model, session: AsyncSession = Depends(get_db)):
    items = await session.execute(select(item_model))
    return items.scalars().all()



async def update_product_quantity(flag, product_id, quantity, session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(Product).where(Product.id == product_id))
    product = result.scalars().first()

    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Продукт с id {product_id} не существует.")

    if flag:
        product.quantity += quantity
    else:
        if product.quantity < quantity:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Уменьшение количества невозможно, так как указанное превышает текущее количество продукта.")
        else:
            product.quantity -= quantity

    await session.commit()
    return product
