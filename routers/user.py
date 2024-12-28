from loguru import logger
from fastapi import Depends, HTTPException, APIRouter
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse

from schemas import UserCreate
from models import User, Product
from routers.utils import create_item, get_items, delete_object, get_db, templates, get_user_by_credentials
from routers.token import get_current_user, create_access_token

router = APIRouter(
    prefix="/user",
    tags=["User"],
)


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


@router.get("/{phone}")
async def get_customer_by_phone(phone: str, session: AsyncSession = Depends(get_db)):
    user = await session.execute(select(User).where(User.phone == phone))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователя с таким номером нет")
    user = user.scalars().first()
    return user


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, session: AsyncSession = Depends(get_db)):
    try:
        existing_user = await get_user_by_credentials(user, session)

        if existing_user:
            token = create_access_token(data={"user_phone": existing_user.phone, "user_name": existing_user.first_name})
            logger.info(f"Пользователь вошёл: {existing_user.phone}, Token: {token}")
            return {"token": token}
        else:
            new_user = await create_item(user, User, session)
            token = create_access_token(data={"user_phone": new_user.phone, "user_name": new_user.first_name})
            logger.info(f"Пользователь создан: {new_user.phone}, Token: {token}")
            return {"token": token}



    except ValidationError as e:
        logger.error(f"Ошибка валидации: {e}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=e.errors())

    except Exception as e:
        logger.exception(f"Произошла непредвиденная ошибка: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Произошла непредвиденная ошибка.")

@router.delete("/remove/{phone}")
async def delete_user(phone: str, session: AsyncSession = Depends(get_db)):
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
