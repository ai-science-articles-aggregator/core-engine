from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer


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


class ArticleResult(BaseModel):
    id: str  # arxiv_id из RAG
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
