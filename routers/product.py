from fastapi import Depends, HTTPException, APIRouter
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.engine.interfaces import DBAPIType
from sqlalchemy.exc import IntegrityError, SQLAlchemyError, DataError, DatabaseError, DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.responses import JSONResponse, HTMLResponse

from models.schemas import ProductCreate, UpdateProductQuantity
from models.tables import Product
from services.token import verify_manager_role
from utils import create_item, get_items, update_product_quantity, get_db, delete_product_by_id

router = APIRouter(
    prefix="/products",
    tags=["Product"],
)


@router.post("/product/create", dependencies=[Depends(verify_manager_role)], status_code=status.HTTP_200_OK)
async def create_product(product: ProductCreate, session: AsyncSession = Depends(get_db)):
    try:
        return await create_item(product, Product, session)
    except ValidationError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=e.errors())
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Продукт с id {product.id} уже существует.")
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Ошибка сервера. Не удалось создать продукт: {e}")


@router.get("/")
async def get_products(session: AsyncSession = Depends(get_db)):
    return await get_items(Product, session)


@router.get("/product/{id}", dependencies=[Depends(verify_manager_role)], status_code=status.HTTP_200_OK)
async def get_product_by_id(id: int, session: AsyncSession = Depends(get_db)):
    try:
        product = await session.execute(select(Product).where(Product.id == id))
        product = product.scalars().first()
        if product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Продукт с id {id} не существует.")
        return product
    except SQLAlchemyError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Неверный тип данных")
    except DBAPIError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Ошибка сервера. Не удалось получить продукт.")



@router.get("/product/{name}", dependencies=[Depends(verify_manager_role)])
async def get_product_by_name(name: str, session: AsyncSession = Depends(get_db)):
    try:
        product = await session.execute(select(Product).where(Product.name == name))
        product = product.scalars().first()
        if product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Продукт с названием {name} не существует.")
        return product
    except SQLAlchemyError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Неверный тип данных")


@router.put("/product/update/{id}", dependencies=[Depends(verify_manager_role)], response_class=JSONResponse)
async def update_product_quantity_put(flag: bool, product_id: int, quantity: int,
                                      session: AsyncSession = Depends(get_db)):
    try:
        return await update_product_quantity(flag, product_id, quantity, session)
    except SQLAlchemyError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Неверный тип данных")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/product/set_quantity", dependencies=[Depends(verify_manager_role)])
async def update_product_quantity_patch(update: UpdateProductQuantity, session: AsyncSession = Depends(get_db)):
    try:
        product = await session.execute(select(Product).where(Product.id == update.id))
        product = product.scalars().first()

        if product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Продукт с id {update.id} не существует.")

        if update.quantity < 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Невозможно установить отрицательное количество продукта.")

        product.quantity = update.quantity

        await session.commit()

        return product
    except SQLAlchemyError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Неверный тип данных")


@router.delete("/product/remove_by_id/{id}", dependencies=[Depends(verify_manager_role)])
async def delete_product(id: int, session: AsyncSession = Depends(get_db)):
    try:
        return await delete_product_by_id(session, id)

    except HTTPException as e:
        raise e
    except SQLAlchemyError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Неверный тип данных")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
