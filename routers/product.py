from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.responses import JSONResponse

from schemas import ProductCreate
from models import Product

from routers.utils import create_item, get_items, update_product_quantity, delete_object, get_db

router = APIRouter(
    prefix="/product",
    tags=["Product"],
)


@router.post("/create")
async def create_product(product: ProductCreate, session: AsyncSession = Depends(get_db)):
    try:
        return await create_item(product, Product, session)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Продукт с таким id уже существует.")


@router.get("/")
async def get_products(session: AsyncSession = Depends(get_db)):
    return await get_items(Product, session)


@router.put("/update")
async def update_product_quantity_put(flag: bool, product_id: int, quantity: int,
                                      session: AsyncSession = Depends(get_db)):
    try:
        return await update_product_quantity(flag, product_id, quantity, session)
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Ошибка при обновлении продукта.")


@router.delete("/remove/{product_id}")
async def delete_product(product_id: int, session: AsyncSession = Depends(get_db)):
    product = await delete_object(session, Product, product_id, 'id')
    report = {
        "detail": "Product deleted successfully",
        "product": {
            "name": product.name,
            "price": product.price,
            "quantity": product.quantity
        }
    }
    return JSONResponse(status_code=status.HTTP_200_OK, content=report)
