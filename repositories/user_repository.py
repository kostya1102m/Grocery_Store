from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from starlette import status

from models.tables import User
from models.schemas import UserCreate

class UserRepository:
    async def get_by_phone(self, phone:str, session: AsyncSession) -> User | None:
        result = await session.execute(select(User).where(User.phone == phone))
        return result.scalars().first()

    async def get_all(self, session: AsyncSession) -> Sequence[User]:
        result = await session.execute(select(User))
        return result.scalars().all()

    async def create(self, user_data: UserCreate, session: AsyncSession) -> User:
        try:
            new_user = User(**user_data.model_dump())
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
            return new_user
        except IntegrityError:
            await session.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Покупатель с номером: {user_data.phone} уже существует")

    async def delete(self, phone: str, session: AsyncSession) -> User:
        result = await session.execute(select(User).where(User.phone == phone))
        user = result.scalars().first()
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Покупатель с номером: {phone} не найден")
        await session.delete(user)
        await session.commit()
        return user