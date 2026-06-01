from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer

PaletteKey = Literal[
    "sienna",
    "moss",
    "azure",
    "plum",
    "ochre",
    "teal",
    "rose",
    "forest",
    "slate",
    "amber",
]


class AreaShort(BaseModel):
    """Inline-представление области внутри других ресурсов (например, NotebookListItem)."""

    id: UUID
    slug: str
    name: str
    palette_key: PaletteKey

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("id")
    def serialize_uuid(self, value: UUID) -> str:
        return str(value)


class AreaRead(AreaShort):
    """Полное представление области для GET /areas."""

    created_at: datetime


class AreaCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    palette_key: PaletteKey = "sienna"


class AreaUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=80)
    palette_key: Optional[PaletteKey] = None
