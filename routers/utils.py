
from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.templating import Jinja2Templates

from database import async_session_maker
from models import Product


async def get_db() -> AsyncSession:
    async with async_session_maker() as session:
        yield session

templates = Jinja2Templates(directory="templates")

async def create_item(item_create_model, item_model, session: AsyncSession = Depends(get_db)):
    new_item = item_model(**item_create_model.dict())
    session.add(new_item)
    await session.commit()
    await session.refresh(new_item)
    return new_item

async def delete_object(session: AsyncSession, model, identifier, identifier_field):
    result = await session.execute(select(model).where(getattr(model, identifier_field) == identifier))
    obj = result.scalars().first()

    if obj is None:
        raise HTTPException(status_code=404, detail=f"{model.__name__} с таким идентификатором не существует.")

    await session.delete(obj)
    await session.commit()
    return obj

async def get_items(item_model, session: AsyncSession = Depends(get_db)):
    items = await session.execute(select(item_model))
    return items.scalars().all()


async def update_product_quantity(flag, product_id, quantity, session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(Product).where(Product.id == product_id))
    product = result.scalars().first()

    if product is None:
        raise HTTPException(status_code=404, detail="Продукт с таким id не существует.")

    if flag:
        product.quantity += quantity
    else:
        product.quantity -= quantity

    await session.commit()
    return product
