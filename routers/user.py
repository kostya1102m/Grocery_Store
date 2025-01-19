from fastapi import Depends, HTTPException, APIRouter
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError, DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse, HTMLResponse, Response

from models.schemas import UserCreate, RoleRequest, Token
from models.tables import User, Product, Order
from utils import create_item, get_items, delete_object, get_db, get_user_by_credentials, manager_templates, \
    customer_templates
from services.token import get_current_user, create_access_token, verify_manager_role

router = APIRouter(
    prefix="/users",
    tags=["User"],
)


@router.get("/", dependencies=[Depends(verify_manager_role)])
async def get_users(session: AsyncSession = Depends(get_db)):
    return await get_items(User, session)


@router.get("/user/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/user/role", status_code=status.HTTP_201_CREATED)
async def set_user_role(
        role_request: RoleRequest,
        response: Response = None
):
    role = role_request.role
    token = create_access_token(data={"role": role})
    response.set_cookie(key="token", value=token)
    return {"token": token}


@router.get("/user/customer_page", response_class=HTMLResponse)
async def customer_page(
        request: Request,
        session: AsyncSession = Depends(get_db)
):
    products = await get_items(Product, session)
    return customer_templates.TemplateResponse(
        "products.html",
        {
            "request": request,
            "products": products
        }
    )


@router.get("/user/manager_page/products", response_class=HTMLResponse)
async def get_products_page(
        request: Request,
        session: AsyncSession = Depends(get_db)
):
    products = await get_items(Product, session)
    return manager_templates.TemplateResponse(
        "products.html",
        {
            "request": request,
            "products": products
        }
    )


@router.get("/user/manager_page/orders", response_class=HTMLResponse)
async def get_order_page(
        request: Request,
        session: AsyncSession = Depends(get_db)
):
    orders = await get_items(Order, session)
    return manager_templates.TemplateResponse(
        "orders.html",
        {
            "request": request,
            "orders": orders
        }
    )


@router.get("/user/manager_page/users", response_class=HTMLResponse)
async def get_users_page(
        request: Request,
        session: AsyncSession = Depends(get_db)
):
    users = await get_items(User, session)
    return manager_templates.TemplateResponse(
        "users.html",
        {
            "request": request,
            "users": users
        }
    )


@router.get("/user/{phone}", dependencies=[Depends(verify_manager_role)])
async def get_customer_by_phone(
        phone: str,
        session: AsyncSession = Depends(get_db)
):
    try:
        user = await session.execute(select(User).where(User.phone == phone))
        user = user.scalars().first()
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Покупателя с номером {phone} не существует.")
        return user
    except SQLAlchemyError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Неверный тип данных")
    except DBAPIError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Ошибка сервера. Не удалось получить продукт.")


@router.post("/user/create", status_code=status.HTTP_201_CREATED)
async def create_user(
        user: UserCreate,
        role_request: RoleRequest = None,
        session: AsyncSession = Depends(get_db),
        response: Response = None
):
    try:
        existing_user = await get_user_by_credentials(user, session)

        if existing_user:
            user_data = existing_user
        else:
            user_data = await create_item(user, User, session)

        if role_request is not None:
            access_token = create_access_token(
                data={
                    "user_phone": user_data.phone,
                    "user_name": user_data.first_name,
                    "role": role_request.role
                }
            )
            response.set_cookie(key="token", value=access_token)
            return Token(access_token=access_token)
        else:
            return user_data


    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=e.errors())
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Пользователь с номером {user.phone} уже существует")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=str(e))


@router.delete("/user/remove_by_phone/{phone}", dependencies=[Depends(verify_manager_role)])
async def delete_user(
        phone: str,
        session: AsyncSession = Depends(get_db)
):
    user = await delete_object(session, User, phone, 'phone')
    report = {
        "detail": "User  deleted successfully",
        "user": {
            "last_name": user.last_name,
            "first_name": user.first_name,
            "patronymic": user.patrynomic
        }
    }
    return JSONResponse(status_code=status.HTTP_200_OK, content=report)
