from fastapi import Depends, HTTPException, APIRouter
from loguru import logger
from sqlalchemy import select, func, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from jose import jwt
from starlette.responses import JSONResponse
from datetime import datetime

from config import settings
from models import Order, User, Product, Ordered_product
from routers.utils import get_items, get_db, delete_object
from routers.token import ALGORITHM
from schemas import OrderRequest

router = APIRouter(
    prefix="/order",
    tags=["Order"],
)


@router.get("/")
async def get_orders(session: AsyncSession = Depends(get_db)):
    return await get_items(Order, session)


@router.get("/{user_phone}")
async def get_user_orders(user_phone: str, session: AsyncSession = Depends(get_db)):
    try:
        user = await session.execute(select(User).where(User.phone == user_phone))
        user = user.scalars().first()

        if user is None:
            logger.exception(f"Пользователь с номером: {user_phone} не найден")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователя с таким номером нет")

        orders = await session.execute(select(Order).where(Order.customer_phone == user.phone))
        orders = orders.scalars().all()
        return orders
    except IntegrityError as e:
        logger.error(f"Произошла непредвиденная ошибка: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Произошла непредвиденная ошибка")


@router.get("/{order_id}")
async def get_order_by_id(order_id: int, session: AsyncSession = Depends(get_db)):
    try:
        order = await session.execute(select(Order).where(Order.id == order_id))
        order = order.scalars().first()

        if order is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заказ с таким id не существует")

        return order
    except IntegrityError as e:
        logger.exception(f"Произошла непредвиденная ошибка: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутренняя ошибка сервера")


@router.get("/report/{phone}")
async def create_user_report(phone: str, session: AsyncSession = Depends(get_db)):
    try:
        user = await session.execute(select(User).where(User.phone == phone))
        user = user.scalars().first()

        if user is None:
            logger.info(f"Пользователь с номером: {phone} не найден")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователя с таким номером нет")

        orders_query = select(Order).where(Order.customer_phone == user.phone)
        orders = (await session.execute(orders_query)).scalars().all()

        total_orders = len(orders)
        total_revenue = sum(order.total for order in orders) if total_orders > 0 else 0
        average_check = total_revenue / total_orders if total_orders > 0 else 0

        most_popular_product_query = (
            select(Ordered_product.product_id, func.count(Ordered_product.product_id).label("total_quantity"))
            .join(Order, Order.id == Ordered_product.order_id)
            .where(Order.customer_phone == phone)
            .group_by(Ordered_product.product_id)
            .order_by(func.count(Ordered_product.product_id).desc())
            .limit(1)
        )
        most_popular_product = (await session.execute(most_popular_product_query)).one_or_none()
        most_popular_product_id = most_popular_product[0] if most_popular_product else None

        most_popular_product_name = None
        if most_popular_product_id:
            product_query = select(Product.name).where(Product.id == most_popular_product_id)
            most_popular_product_name = (await session.execute(product_query)).scalars().first()

        report = {
            "ФИО": f"{user.last_name} {user.first_name} {user.patrynomic}",
            "Всего заказов": total_orders,
            "Средний чек": float(average_check) if total_orders > 0 else 0,
            "Общая сумма покупок": float(total_revenue),
            "Часто покупаемый продукт": most_popular_product_name
        }

        return JSONResponse(status_code=status.HTTP_200_OK, content=report)

    except IntegrityError as e:
        logger.exception(f"Произошла непредвиденная ошибка: {e}")
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content={"detail": "Внутренняя ошибка сервера"})


@router.get("/report/from/{from_date}/to/{to_date}")
async def create_report_from_date_to_date(from_date: str, to_date: str, session: AsyncSession = Depends(get_db)):
    try:
        from_date_dt = datetime.strptime(from_date, '%Y-%m-%d %H:%M:%S.%f')
        to_date_dt = datetime.strptime(to_date, '%Y-%m-%d %H:%M:%S.%f')

        orders_query = (select(Order)
                        .where(Order.date.between(from_date_dt, to_date_dt)))
        orders = (await session.execute(orders_query)).scalars().all()

        total_orders = len(orders)
        total_revenue = sum(order.total for order in orders) if total_orders > 0 else 0
        average_check = total_revenue / total_orders if total_orders > 0 else 0

        most_popular_product_query = (
            select(Ordered_product.product_id, func.sum(Ordered_product.chosen_quantity).label("total_quantity"))
            .join(Order, Order.id == Ordered_product.order_id)
            .where(Order.date.between(from_date_dt, to_date_dt))
            .group_by(Ordered_product.product_id)
            .order_by(text("total_quantity DESC"))
            .limit(1)
        )
        most_popular_product = (await session.execute(most_popular_product_query)).one_or_none()
        most_popular_product_id = most_popular_product[0] if most_popular_product else None

        most_popular_product_name = None
        if most_popular_product_id:
            product_query = select(Product.name).where(Product.id == most_popular_product_id)
            most_popular_product_name = (await session.execute(product_query)).scalars().first()

        report = {
            "Период": f"{from_date} - {to_date}",
            "Всего заказов": total_orders,
            "Общая сумма покупок": float(total_revenue),
            "Средний чек": float(average_check),
            "Самый продаваемый продукт": most_popular_product_name
        }

        return JSONResponse(status_code=status.HTTP_200_OK, content=report)

    except ValueError:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content={"error": "Неверный формат даты. Используйте YYYY-MM-DD-HH-MM-SS.ffffff"})
    except IntegrityError:
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content={"error": "Ошибка соединения с базой данных"})


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_order(order_request: OrderRequest, session: AsyncSession = Depends(get_db)):
    if order_request.token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Пользователь не авторизован")

    payload = jwt.decode(order_request.token, settings.secret_key, algorithms=[ALGORITHM])
    phone: str = payload.get("user_phone")
    first_name: str = payload.get("user_name")

    user = await session.execute(select(User).where(User.phone == phone))
    user = user.scalars().first()

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователя с таким номером нет")

    order = Order(
        customer_phone=phone,
        customer_name=first_name,
        date=datetime.now(),
        total=0
    )
    session.add(order)
    await session.flush()

    total_price = 0
    purchased_products = []

    for item in order_request.quantities:
        product = await session.execute(select(Product).where(Product.id == item.product_id))
        product = product.scalars().first()
        if product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Продукт с таким id не существует.")

        if product.quantity < item.chosen_quantity:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Недостаточно товара на складе.")

        product.quantity -= item.chosen_quantity

        ordered_product = Ordered_product(
            order_id=order.id,
            product_id=item.product_id,
            chosen_quantity=item.chosen_quantity
        )
        session.add(ordered_product)

        counted_price = product.price * item.chosen_quantity
        total_price += counted_price

        purchased_products.append({
            'id товара': item.product_id,
            'Название': product.name,
            'Количество': item.chosen_quantity,
            'Цена за штуку': float(product.price),
            'Итоговая цена': float(counted_price)
        })

    order.total = total_price

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при выполнении покупки. Попробуйте снова."
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": "Покупка успешно завершена",
            "order_id": order.id,
            "total_price": float(order.total),
            "purchased_items": purchased_products
        }
    )


@router.delete("/remove/{order_id}")
async def delete_order(order_id: int, session: AsyncSession = Depends(get_db)):
    order = await delete_object(session, Order, order_id, 'id')
    return JSONResponse(status_code=status.HTTP_200_OK,
    content={
        "detail": "Заказ успешно удалён",
        "order": {
            "id": order.id,
            "Имя покупателя": order.customer_name,
            "Номер покупателя": order.customer_phone,
            "Дата заказа": order.date,
            "Общая сумма заказа": float(order.total)
        }
    })
