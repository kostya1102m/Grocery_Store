from typing import List
from pydantic import BaseModel, Field, field_validator


class UserCreate(BaseModel):
    phone: str = Field(..., min_length=11, max_length=11)
    first_name: str = Field(..., min_length=2, max_length=15)
    last_name: str = Field(..., min_length=2, max_length=15)
    patrynomic: str = Field(..., min_length=2, max_length=15)

    @field_validator('phone')
    @classmethod
    def phone_validator(cls, v):
        if not v.isdigit() or v[0] != "8":
            raise ValueError("Номер должен начинаться с 8 и содержать только цифры")
        return v

    @field_validator('first_name', 'last_name', 'patrynomic')
    @classmethod
    def fio_validator(cls, v):
        if len(v) < 2 or not v[0].isupper() or not v[1:].islower() or not v.isalpha():
            raise ValueError(
                "Фамилия, имя и отчество должны начинаться с заглавной буквы, содержать только буквы и не содержать другие прописные буквы.")
        return v


class ProductCreate(BaseModel):
    id: int = Field(..., gt=0)
    name: str = Field(..., min_length=2, max_length=15)
    price: float = Field(..., gt=0)
    quantity: int = Field(..., gt=0)


class OrderItem(BaseModel):
    product_id: int
    chosen_quantity: int


class OrderRequest(BaseModel):
    token: str
    quantities: List[OrderItem]

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class RoleRequest(BaseModel):
    role: str