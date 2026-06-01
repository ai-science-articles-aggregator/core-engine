from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class TagShort(BaseModel):
    """Inline-представление тега внутри других ресурсов."""

    id: UUID
    slug: str
    name: str

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("id")
    def serialize_uuid(self, value: UUID) -> str:
        return str(value)


class TagWithCount(TagShort):
    """Для GET /tags — с числом тетрадей, использующих тег."""

    notebook_count: int = 0


class TagRename(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
