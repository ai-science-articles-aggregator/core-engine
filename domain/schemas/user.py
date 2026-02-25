from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_serializer

class UserBase(BaseModel):
    username: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Unique username / Уникальное имя пользователя"
    )
    email: EmailStr = Field(
        ...,
        description="User email address / Email адрес пользователя"
    )
    full_name: Optional[str] = Field(
        None,
        max_length=255,
        description="User's full name / Полное имя пользователя"
    )

class UserCreate(UserBase):
    """DTO для создания пользователя (input)"""
    password: str

class UserResponse(UserBase):
    """DTO для ответа API (output)"""
    id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

    @field_serializer("id")
    def serialize_uuid(self, value: UUID) -> str:
        return str(value)