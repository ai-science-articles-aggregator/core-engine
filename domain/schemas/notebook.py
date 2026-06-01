from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from .area import AreaShort
from .tag import TagShort
from .user import UserShort

Visibility = Literal["private", "shared", "public"]


class NotebookCreate(BaseModel):
    """Payload для POST /notebooks/create и PUT /notebooks/:id.

    Поля area_id / tags / visibility принимаются фронтом всегда, даже если
    соответствующая бизнес-логика ещё не реализована (см. P2.1 / P2.2 / P2.3).
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Имя тетради",
    )
    description: Optional[str] = Field(
        None,
        max_length=1000,
        description="Описание тетради",
    )
    area_id: Optional[UUID] = Field(
        None,
        description="ID научной области (должна принадлежать current_user)",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Имена тегов; на бэке upsert-ятся в личную коллекцию",
    )
    visibility: Visibility = Field(
        default="private",
        description="Уровень доступа",
    )


class NotebookListItem(BaseModel):
    """Расширенный ответ для GET /notebooks и POST /notebooks/create.

    Поля area / tags / shared_by / sources_count / notes_count наполняются
    по мере реализации соответствующих модулей; пока могут быть пустыми /
    дефолтными — структура стабильна для фронта.
    """

    id: UUID
    name: str
    description: Optional[str] = None
    area: Optional[AreaShort] = None
    tags: list[TagShort] = Field(default_factory=list)
    visibility: Visibility = "private"
    is_owner: bool = True
    shared_by: Optional[UserShort] = None
    sources_count: int = 0
    notes_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("id")
    def serialize_uuid(self, value: UUID) -> str:
        return str(value)


# ---- алиас на старое имя, чтобы не ломать существующие импорты ----
NotebookResponse = NotebookListItem
NotebookListResponse = NotebookListItem


class ArticleResult(BaseModel):
    id: str
    title: str
    authors: str
    score: float


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(default=10, ge=1, le=50)


class SearchResponse(BaseModel):
    query: str
    articles: list[ArticleResult]


class SummarizeRequest(BaseModel):
    article_ids: list[str] = Field(..., min_length=1, max_length=50)
    query: str = Field(..., min_length=1, max_length=500)
