from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_serializer


class NotifSettings(BaseModel):
    digest_weekly: bool = True
    new_citations: bool = True
    shared_activity: bool = False


class UserBase(BaseModel):
    email: EmailStr = Field(
        ...,
        description="University email / Университетский email",
    )
    first_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="First name / Имя",
    )
    last_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Last name / Фамилия",
    )
    department: Optional[str] = Field(
        None,
        max_length=255,
        description="Faculty / Department",
    )


class UserCreate(UserBase):
    """DTO для регистрации (input)."""

    password: str = Field(..., min_length=6, max_length=255)


class UserUpdate(BaseModel):
    """DTO для PATCH /auth/profile — все поля опциональны."""

    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    department: Optional[str] = Field(None, max_length=255)
    notif_settings: Optional[NotifSettings] = None


class UserResponse(UserBase):
    """DTO для GET /auth/profile."""

    id: UUID
    notif_settings: NotifSettings
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("id")
    def serialize_uuid(self, value: UUID) -> str:
        return str(value)


class UserShort(BaseModel):
    """Минимальное inline-представление (например, для shared_by)."""

    id: UUID
    first_name: str
    last_name: str

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("id")
    def serialize_uuid(self, value: UUID) -> str:
        return str(value)
