from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_serializer


class NotebookBase(BaseModel):
    name: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="The name of the notebook / Имя блокнота",
    )
    description: Optional[str] = Field(
        None,
        min_length=3,
        max_length=1000,
        description="The description of the notebook / Описание блокнота",
    )


class NotebookCreate(NotebookBase):
    pass


class NotebookResponse(NotebookBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("id", "user_id")
    def serialize_uuid(self, value: UUID) -> str:
        return str(value)


class NotebookListResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("id")
    def serialize_uuid(self, value: UUID) -> str:
        return str(value)
