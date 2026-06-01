from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer

ChatRole = Literal["user", "assistant", "system"]


class ChatCitation(BaseModel):
    article_id: str
    label: str
    frag: str = ""


class ChatMessageRead(BaseModel):
    id: UUID
    role: ChatRole
    text: str
    citations: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("id")
    def serialize_uuid(self, value: UUID) -> str:
        return str(value)


class ChatMessageCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000)
