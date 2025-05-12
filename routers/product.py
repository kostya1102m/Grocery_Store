from fastapi import Depends, HTTPException, APIRouter
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.responses import JSONResponse

from models.schemas import ProductCreate, UpdateProductQuantity
from models.tables import Product
from services.token import verify_manager_role
from utils import create_item, get_items, update_product_quantity, get_db, delete_product_by_id

router = APIRouter(
    prefix="/products",
    tags=["Product"],
)


@router.post("/product/create", dependencies=[Depends(verify_manager_role)])
async def create_product(product: ProductCreate, session: AsyncSession = Depends(get_db)):
    try:
        product = await create_item(product, Product, session)
        return JSONResponse(status_code=status.HTTP_200_OK,
                            content={"detail": "Товар успешно добавлен в базу данных",
                                     "product": {
                                         "id": product.id,
                                         "name": product.name,
                                         "price": float(product.price),
                                         "quantity": product.quantity
                                     }})
    except ValidationError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=e.errors())
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Товар с ID: {product.id} уже существует.")
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Ошибка сервера. Не удалось создать товар: {e}")


@router.get("/")
async def get_products(session: AsyncSession = Depends(get_db)):
    return await get_items(Product, session)


@router.get("/product/{id}")
async def get_product_by_id(id: int, session: AsyncSession = Depends(get_db)):
    try:
        product = await session.execute(select(Product).where(Product.id == id))
        product = product.scalars().first()
        if product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Товар с ID: {id} не найден.")
        return product

    except HTTPException as NotFound:
        raise NotFound

    except SQLAlchemyError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Необрабатываемое значение: {id}.")

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Ошибка сервера. Не удалось найти товар: {e}")


@router.get("/product/name/{name}")
async def get_product_by_name(name: str, session: AsyncSession = Depends(get_db)):
    try:
        product = await session.execute(select(Product).where(Product.name == name))
        product = product.scalars().first()
        if product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Товар с названием: {name} не найден.")
        return product

    except HTTPException as NotFound:
        await session.rollback()
        raise NotFound

    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Необрабатываемое значение: {name}.")
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Ошибка сервера. Не удалось найти товар: {e}")


@router.put("/product/update/{id}", dependencies=[Depends(verify_manager_role)], response_class=JSONResponse)
async def update_product_quantity_put(flag: bool, product_id: int, quantity: int,
                                      session: AsyncSession = Depends(get_db)):
    try:
        return await update_product_quantity(flag, product_id, quantity, session)

    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Тип данных ID и Количества должен быть INT32")
    except Exception as e:
        await session.rollback()
        raise e


@router.put("/product/set_quantity", dependencies=[Depends(verify_manager_role)])
async def update_product_quantity_patch(update: UpdateProductQuantity, session: AsyncSession = Depends(get_db)):
    try:
        product = await session.execute(select(Product).where(Product.id == update.id))
        product = product.scalars().first()

        if product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Товар с ID: {update.id} не найден.")

        if update.quantity < 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Невозможно установить отрицательное количество товара.")

        product.quantity = update.quantity

        await session.commit()

        return JSONResponse(status_code=status.HTTP_200_OK, content={"detail": "Количество товара успешно обновлено"})

    except ValidationError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=e.errors())

    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Типы ID и Количество должны быть INT32.")


    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Ошибка сервера. Не удалось обновить количество товара.")


@router.delete("/product/remove_by_id/{id}", dependencies=[Depends(verify_manager_role)])
async def delete_product(id: int, session: AsyncSession = Depends(get_db)):
    try:
        product = await delete_product_by_id(session, id)
        report = {
            "detail": "Товар успешно удалён",
            "product": {
                "id": product.id,
                "name": product.name,
                "price": float(product.price),
                "quantity": product.quantity
            }
        }
        return JSONResponse(status_code=status.HTTP_200_OK, content=report)

    except SQLAlchemyError:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Необрабатываемое значение: {id}.")
