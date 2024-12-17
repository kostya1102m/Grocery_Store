from fastapi import FastAPI, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import JSONResponse,  FileResponse, RedirectResponse
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.staticfiles import StaticFiles

from database import async_session_maker
from schemas import UserCreate, ProductCreate
from models import User, Product

app = FastAPI()


app.mount('/static', StaticFiles(directory='static'), 'static')

async def get_db() -> AsyncSession:
    async with async_session_maker() as session:
        yield session

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
    product = await session.execute(select(Product).where(Product.id == product_id))
    product = product.scalars().first()
    if flag:
        product.quantity += quantity
    else:
        product.quantity -= quantity
    await session.commit()
    return product

@app.post("/user/")
async def create_user(user: UserCreate, session: AsyncSession = Depends(get_db)):
    existing_user = await session.execute(select(User).where(User.phone == user.phone))
    existing_user_instance = existing_user.scalars().first()

    if existing_user_instance:
        # Если пользователь с таким номером телефона существует, проверяем ФИО
        if (existing_user_instance.first_name == user.first_name and
                existing_user_instance.last_name == user.last_name and
                existing_user_instance.patrynomic == user.patrynomic):
            # Если все поля совпадают, возвращаем сообщение о входе
            return {"message": "Покупатель вошел в систему", "user_id": user.phone}
        else:
            # Если номер телефона совпадает, но ФИО различаются, возвращаем ошибку
            raise HTTPException(status_code=400,
                                detail="Пользователь с таким номером телефона уже существует, но ФИО не совпадают")

    return await create_item(user, User, session)

@app.post("/product/")
async def create_product(product: ProductCreate, session: AsyncSession = Depends(get_db)):
    return await create_item(product, Product, session)

@app.get("/", response_class=HTMLResponse)
async def get_main_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/users/")
async def get_users(session: AsyncSession = Depends(get_db)):
    return await get_items(User, session)

@app.get("/products/")
async def get_products(session: AsyncSession = Depends(get_db)):
    return await get_items(Product, session)

@app.get("/customer_page/", response_class=HTMLResponse)
async def get_customer_page(request: Request, session: AsyncSession = Depends(get_db)):
    # Получаем все продукты из базы данных
    products = await get_items(Product, session)
    # Возвращаем страницу с продуктами
    return templates.TemplateResponse("customer.html", {"request": request, "products": products})

@app.put("/update_product/")
async def update_product_quantity_put(flag: bool, product_id: int, quantity: int, session: AsyncSession = Depends(get_db)):
    return await update_product_quantity(flag, product_id, quantity, session)

@app.delete("/delete_user/")
async def delete_user(phone: str, session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(User).where(User.phone == phone))
    user = result.scalars().first()

    # Если пользователь не найден, возвращаем ошибку 404
    if user is None:
        raise HTTPException(status_code=404, detail="User  not found")

    # Удаляем пользователя и коммитим изменения
    await session.delete(user)
    await session.commit()

    return {"detail": "User  deleted successfully"}


@app.delete("/delete_product/")
async def delete_product(product_id: str, session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(Product).where(Product.id == product_id))
    product = result.scalars().first()

    # Если пользователь не найден, возвращаем ошибку 404
    if product is None:
        raise HTTPException(status_code=404, detail="User  not found")

    # Удаляем пользователя и коммитим изменения
    await session.delete(product)
    await session.commit()

    return {"detail": "Product  deleted successfully"}

@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"errors": [{"loc": error["loc"], "msg": error["msg"]} for error in exc.errors()]},
    )