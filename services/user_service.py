from fastapi import HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.responses import JSONResponse
from typing import Sequence

from models.schemas import UserCreate, RoleRequest, Token
from models.tables import User
from repositories.user_repository import UserRepository
from services.token import create_access_token

class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def get_all_users(self, session: AsyncSession) -> Sequence[User]:
        return await self.user_repository.get_all(session)

    async def get_user_by_phone(self, phone: str, session: AsyncSession) -> User:
        user = await self.user_repository.get_by_phone(phone, session)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Пользователь с номером: {phone} не найден.")
        return user

    async def create_user(
        self,
        user_data: UserCreate,
        role_request: RoleRequest | None,
        response: Response | None,
        session: AsyncSession
    ):
        user = await self.user_repository.get_by_phone(user_data.phone, session)
        if user:
            user_data = user
        else:
            user_data = await self.user_repository.create(user_data, session)

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
            return JSONResponse(status_code=status.HTTP_200_OK, content={
                "detail": "Покупатель успешно добавлен в базу данных",
                "user": {
                    "last_name": user_data.last_name,
                    "first_name": user_data.first_name,
                    "patrynomic": user_data.patrynomic,
                    "phone": user_data.phone
                }
            })

    async def delete_user(self, phone: str, session: AsyncSession) -> JSONResponse:
        user = await self.user_repository.delete(phone, session)
        return JSONResponse(status_code=status.HTTP_200_OK, content={
            "detail": "Покупатель успешно удалён из базы данных",
            "user": {
                "last_name": user.last_name,
                "first_name": user.first_name,
                "patrynomic": user.patrynomic,
                "phone": user.phone
            }
        })

