from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_serializer, model_validator

ShareRole = Literal["viewer", "commenter", "editor"]


class ShareUserInfo(BaseModel):
    """Минимум полей о получателе шара."""

    id: UUID
    email: str
    first_name: str
    last_name: str

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("id")
    def serialize_uuid(self, value: UUID) -> str:
        return str(value)


class ShareCreate(BaseModel):
    """POST /notebooks/:id/shares — нужен либо user_id, либо user_email."""

    user_id: Optional[UUID] = None
    user_email: Optional[EmailStr] = None
    role: ShareRole = "viewer"

    @model_validator(mode="after")
    def _one_of_user(self):
        if not self.user_id and not self.user_email:
            raise ValueError("Either user_id or user_email is required")
        if self.user_id and self.user_email:
            raise ValueError("Provide either user_id or user_email, not both")
        return self


class ShareUpdateMe(BaseModel):
    """PATCH /notebooks/:id/shares/me — recipient меняет свой area_id."""

    area_id: Optional[UUID] = None


class ShareRead(BaseModel):
    notebook_id: UUID
    user: ShareUserInfo
    role: ShareRole
    area_id: Optional[UUID] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("notebook_id", "area_id", when_used="json")
    def _ser_uuid(self, value: Optional[UUID]) -> Optional[str]:
        return str(value) if value else None
