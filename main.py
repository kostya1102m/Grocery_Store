
from fastapi import FastAPI, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import FileResponse
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse
from starlette.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta

from database import async_session_maker
from schemas import UserCreate, ProductCreate
from models import User, Product
from config import settings

app = FastAPI()

app.mount('/static', StaticFiles(directory='static'), 'static')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:7000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_db() -> AsyncSession:
    async with async_session_maker() as session:
        yield session

async def get_current_user(token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        phone: str = payload.get("sub")
        if phone is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = await session.execute(select(User).where(User.phone == phone))
    user = user.scalars().first()
    if user is None:
        raise credentials_exception
    return user

templates = Jinja2Templates(directory="templates")


async def create_item(item_create_model, item_model, session: AsyncSession = Depends(get_db)):
    new_item = item_model(**item_create_model.dict())
    session.add(new_item)
    await session.commit()
    await session.refresh(new_item)
    return new_item


async def get_items(item_model, session: AsyncSession = Depends(get_db)):
    items = await session.execute(select(item_model))
    return items.scalars().all()


async def update_product_quantity(flag, product_id, quantity, session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(Product).where(Product.id == product_id))
    product = result.scalars().first()

    if product is None:
        raise HTTPException(status_code=404, detail="Продукт с таким id не существует.")

    if flag:
        product.quantity += quantity
    else:
        product.quantity -= quantity

    await session.commit()
    return product

@app.post("/user/")
async def create_user(user: UserCreate, session: AsyncSession = Depends(get_db)):
    try:
        new_user = await create_item(user, User, session)
        # Генерация токена
        access_token = create_access_token(data={"sub": new_user.phone})  # Используйте уникальный идентификатор
        return {"token": access_token}
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Пользователь с таким номером уже существует.")


@app.post("/product/")
async def create_product(product: ProductCreate, session: AsyncSession = Depends(get_db)):
    try:
        return await create_item(product, Product, session)
    except IntegrityError:
        await session.rollback()  # Откат транзакции
        raise HTTPException(status_code=400, detail="Продукт с таким id уже существует.")

@app.get("/")
async def root():
    return FileResponse('templates/index.html')

@app.get("/me/")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.get("/users/")
async def get_users(session: AsyncSession = Depends(get_db)):
    return await get_items(User, session)

@app.get("/products/")
async def get_products(session: AsyncSession = Depends(get_db)):
    return await get_items(Product, session)

@app.get("/customer_page/", response_class=HTMLResponse)
async def customer_page(request: Request, session: AsyncSession = Depends(get_db)):
    products = await get_items(Product, session)
    return templates.TemplateResponse("customer.html", {"request": request, "products": products})

@app.put("/update_product/")
async def update_product_quantity_put(flag: bool, product_id: int, quantity: int,
                                      session: AsyncSession = Depends(get_db)):
    try:
        return await update_product_quantity(flag, product_id, quantity, session)
    except IntegrityError:
        await session.rollback()  # Откат транзакции
        raise HTTPException(status_code=400, detail="Ошибка при обновлении продукта.")

@app.delete("/delete_user/")
async def delete_user(phone: str, session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(User).where(User.phone == phone))
    user = result.scalars().first()

    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь с таким номером не существует.")

    await session.delete(user)
    await session.commit()
    return {
        "detail": "User  deleted successfully",
        "user": {
            "last_name": user.last_name,
            "first_name": user.first_name,
            "patronymic": user.patrynomic
        }
    }

@app.delete("/delete_product/")
async def delete_product(product_id: int, session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(Product).where(Product.id == product_id))
    product = result.scalars().first()

    if product is None:
        raise HTTPException(status_code=404, detail="Продукт с таким id не существует.")

    await session.delete(product)
    await session.commit()
    return {"detail": "Product deleted successfully",
            "product": {
                "name": product.name,
                "price": product.price,
                "quantity": product.quantity
            }
    }


@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(status_code=400, content={"detail": exc.errors()})

