from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SourceRead(BaseModel):
    """Source = id статьи из RAG + статус selected. Метаданные у нас не хранятся."""

    article_id: str
    selected: bool
    added_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SourceCreate(BaseModel):
    article_ids: list[str] = Field(..., min_length=1, max_length=200)


class SourceToggle(BaseModel):
    selected: bool
