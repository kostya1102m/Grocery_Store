from fastapi import Depends, HTTPException, APIRouter
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.responses import JSONResponse

from models.schemas import ProductCreate
from models.tables import Product
from services.token import verify_manager_role

from utils import create_item, get_items, update_product_quantity, delete_object, get_db

router = APIRouter(
    prefix="/products",
    tags=["Product"],
)


@router.post("/product/create", dependencies=[Depends(verify_manager_role)])
async def create_product(product: ProductCreate, session: AsyncSession = Depends(get_db)):
    try:
        return await create_item(product, Product, session)
    except ValidationError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=e.errors())
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Ошибка сервера. Не удалось создать продукт.")


@router.get("/")
async def get_products(session: AsyncSession = Depends(get_db)):
    return await get_items(Product, session)


@router.put("/product/update/{product_id}", dependencies=[Depends(verify_manager_role)])
async def update_product_quantity_put(flag: bool, product_id: int, quantity: int,
                                      session: AsyncSession = Depends(get_db)):
    return await update_product_quantity(flag, product_id, quantity, session)


@router.delete("/product/remove_by_id/{product_id}", dependencies=[Depends(verify_manager_role)])
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
