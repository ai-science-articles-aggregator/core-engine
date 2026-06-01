from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ArticleRead(BaseModel):
    """Метаданные статьи для отображения в карточке source'а на фронте."""

    id: str
    arxiv_id: Optional[str] = None
    title: Optional[str] = None
    authors: Optional[str] = None
    abstract: Optional[str] = None
    published: Optional[datetime] = None
    categories: Optional[str] = None
    primary_category: Optional[str] = None
    doi: Optional[str] = None
    journal_ref: Optional[str] = None
    num_pages: Optional[int] = None
    pdf_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ArticlesBatchRequest(BaseModel):
    """POST /api/v1/articles/batch — список id-шников из RAG."""

    ids: list[str] = Field(..., min_length=1, max_length=500)
