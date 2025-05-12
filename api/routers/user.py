from fastapi import Depends, APIRouter, Request, Response
from starlette.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from models.schemas import UserCreate, RoleRequest
from models.tables import User, Product
from services.user_service import UserService
from repositories.user_repository import UserRepository
from services.token import get_current_user, verify_manager_role
from utils import get_db, customer_templates, manager_templates, get_items

router = APIRouter(
    prefix="/users",
    tags=["User"],
)

def get_user_service():
    user_repository = UserRepository()
    return UserService(user_repository)

@router.get("/", dependencies=[Depends(verify_manager_role)])
async def get_users(
    session: AsyncSession = Depends(get_db),
    user_service: UserService = Depends(get_user_service)
):
    return await user_service.get_all_users(session)

@router.get("/user/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/user/role", status_code=status.HTTP_201_CREATED)
async def set_user_role(
    role_request: RoleRequest,
    response: Response
):
    from services.token import create_access_token
    token = create_access_token(data={"role": role_request.role})
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
    from models.tables import Order
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
    session: AsyncSession = Depends(get_db),
    user_service: UserService = Depends(get_user_service)
):
    users = await user_service.get_all_users(session)
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
    session: AsyncSession = Depends(get_db),
    user_service: UserService = Depends(get_user_service)
):
    return await user_service.get_user_by_phone(phone, session)

@router.post("/user/create", status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate,
    role_request: RoleRequest | None = None,
    session: AsyncSession = Depends(get_db),
    response: Response = None,
    user_service: UserService = Depends(get_user_service)
):
    return await user_service.create_user(user, role_request, response, session)

@router.delete("/user/remove_by_phone/{phone}", dependencies=[Depends(verify_manager_role)])
async def delete_user(
    phone: str,
    session: AsyncSession = Depends(get_db),
    user_service: UserService = Depends(get_user_service)
):
    return await user_service.delete_user(phone, session)