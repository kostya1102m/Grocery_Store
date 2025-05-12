from fastapi import Depends, HTTPException, APIRouter
from pydantic import ValidationError
from sqlalchemy import select, func, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from jose import jwt
from starlette.requests import Request
from starlette.responses import JSONResponse, HTMLResponse
from datetime import datetime

from config import settings
from models.tables import Order, User, Product, Ordered_product
from utils import get_items, get_db, delete_object, customer_templates, manager_templates, get_order_products
from services.token import ALGORITHM, verify_manager_role
from models.schemas import OrderRequest

router = APIRouter(
    prefix="/orders",
    tags=["Order"],
)


@router.get("/", dependencies=[Depends(verify_manager_role)])
async def get_orders(session: AsyncSession = Depends(get_db)):
    return await get_items(Order, session)


@router.get("/{phone}", dependencies=[Depends(verify_manager_role)])
async def get_user_orders(phone: str, session: AsyncSession = Depends(get_db)):
    try:
        user = await session.execute(select(User).where(User.phone == phone))
        user = user.scalars().first()

        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Покупатель с номером: {phone} не найден.")

        orders = await session.execute(select(Order).where(Order.customer_phone == user.phone))
        orders = orders.scalars().all()

        if len(orders) == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Данный покупатель заказов не совершал.")

        return orders

    except HTTPException as NotFound:
        raise NotFound

    except SQLAlchemyError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Необрабатываемое значение: {phone}.")

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Ошибка сервера. Не удалось найти заказы: {e}")


@router.get("/order/{id}", dependencies=[Depends(verify_manager_role)])
async def get_order_by_id(id: int, session: AsyncSession = Depends(get_db)):
    try:
        order = await session.execute(select(Order).where(Order.id == id))
        order = order.scalars().first()

        if order is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Заказ с ID: {id} не найден.")

        return order

    except HTTPException as NotFound:
        raise NotFound

    except SQLAlchemyError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Необрабатываемое значение: {id}.")

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Ошибка сервера. Не удалось найти заказ: {e}")


@router.get("/order/report/{phone}", response_class=HTMLResponse)
async def create_user_report(phone: str, request: Request, session: AsyncSession = Depends(get_db)):
    try:
        user = await session.execute(select(User).where(User.phone == phone))
        user = user.scalars().first()

        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Покупатель с номером: {phone} не найден.")

        orders_query = select(Order).where(Order.customer_phone == user.phone)
        orders = (await session.execute(orders_query)).scalars().all()

        orders_products = []
        for order in orders:
            products = await get_order_products(order.id, session)
            orders_products.append(products)

        total_orders = len(orders)

        if total_orders == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Данный покупатель заказов не совершал")

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
            "Телефон": user.phone,
            "Всего заказов": total_orders,
            "Средний чек": round(float(average_check), 2) if total_orders > 0 else 0,
            "Общая сумма покупок": round(float(total_revenue), 2),
            "Часто покупаемый товар": most_popular_product_name
        }
        return customer_templates.TemplateResponse("report.html",
                                                   {"request": request, "report": report, "orders": orders_products})
        # return JSONResponse(status_code=status.HTTP_200_OK, content=report)

    except HTTPException as NotFound:
        raise NotFound

    except SQLAlchemyError:
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Необрабатываемое значение: {phone}.")

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Ошибка сервера. Не удалось сформировать отчёт: {e}")


@router.get("/order/report/from/{from_date}/to/{to_date}", dependencies=[Depends(verify_manager_role)])
async def create_report_from_date_to_date(from_date: str, to_date: str, request: Request = None,
                                          session: AsyncSession = Depends(get_db)):
    try:
        from_date_dt = datetime.strptime(from_date, '%Y-%m-%d %H:%M:%S')
        to_date_dt = datetime.strptime(to_date, '%Y-%m-%d %H:%M:%S')

        orders_query = (select(Order)
                        .where(Order.date.between(from_date_dt, to_date_dt)))
        orders = (await session.execute(orders_query)).scalars().all()

        orders_n_products = []
        for order in orders:
            order_products = await get_order_products(order.id, session)
            orders_n_products.append(order_products)

        total_orders = len(orders)

        if total_orders == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="За данный промежуток времени заказы не совершались.")

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
            "Период": f"{from_date} по {to_date}",
            "Всего заказов": total_orders,
            "Общая сумма покупок": round(float(total_revenue), 2),
            "Средний чек": round(float(average_check), 2),
            "Самый продаваемый товар": most_popular_product_name
        }

        # return JSONResponse(status_code=status.HTTP_200_OK, content=report)
        return manager_templates.TemplateResponse("period_report.html",
                                                  {"request": request, "report": report, "orders": orders_n_products})

    except HTTPException as NotFound:
        raise NotFound

    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="Неверный формат даты. Используйте YYYY-MM-DD-HH-MM-SS")

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Ошибка сервера. Не удалось сформировать отчёт: {e}")


@router.post("/order/create", status_code=status.HTTP_201_CREATED)
async def create_order(order_request: OrderRequest, session: AsyncSession = Depends(get_db)):
    if order_request.token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Вы не авторизованы.")

    payload = jwt.decode(order_request.token, settings.secret_key, algorithms=[ALGORITHM])
    phone: str = payload.get("user_phone")
    first_name: str = payload.get("user_name")

    user = await session.execute(select(User).where(User.phone == phone))
    user = user.scalars().first()

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Покупатель с номером: {phone} не найден.")

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
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Товар с ID: {item.product_id} не найден.")

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

    except ValidationError as e:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=e.errors())
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка cервера. Заказ не сформирован."
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


@router.delete("/order/remove_by_id/{id}", dependencies=[Depends(verify_manager_role)])
async def delete_order(id: int, session: AsyncSession = Depends(get_db)):
    try:
        order = await delete_object(session, Order, id, 'id')
        return JSONResponse(status_code=status.HTTP_200_OK,
                            content={
                                "detail": "Заказ успешно удалён",
                                "order": {
                                    "id": order.id,
                                    "Имя покупателя": order.customer_name,
                                    "Номер покупателя": order.customer_phone,
                                    "Дата заказа": order.date.strftime("%Y-%m-%d %H:%M:%S.%f"),
                                    "Общая сумма заказа": float(order.total)
                                }
                            })
    except HTTPException:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Заказ с ID: {id} не найден")

    except SQLAlchemyError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Необрабатываемое значение: {id}.")
