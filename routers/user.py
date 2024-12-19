
from loguru import logger
from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.requests import Request
from starlette.responses import HTMLResponse

from schemas import UserCreate
from models import User, Product
from routers.utils import create_item, get_items, delete_object, get_db, templates
from routers.token import get_current_user, create_access_token

router = APIRouter(
    prefix="/user",
    tags=["user"],
)

@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, session: AsyncSession = Depends(get_db)):
    try:
        new_user = await create_item(user, User, session)
        token = create_access_token(data={"user_phone": new_user.phone})
        logger.info(f"Token : {token}")
        return {"token": token}
    except IntegrityError:
        raise HTTPException(status_code=400, detail="Пользователь с таким номером уже существует.")


@router.get("/")
async def get_users(session: AsyncSession = Depends(get_db)):
    return await get_items(User, session)

@router.get("/me/")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/customer_page/", response_class=HTMLResponse)
async def customer_page(request: Request, session: AsyncSession = Depends(get_db)):
    products = await get_items(Product, session)
    return templates.TemplateResponse("customer.html", {"request": request, "products": products})

@router.delete("/remove")
async def delete_user(phone: str, session: AsyncSession = Depends(get_db)):
    user = await delete_object(session, User, phone, 'phone')
    return {
        "detail": "User  deleted successfully",
        "user": {
            "last_name": user.last_name,
            "first_name": user.first_name,
            "patronymic": user.patrynomic
        }
    }