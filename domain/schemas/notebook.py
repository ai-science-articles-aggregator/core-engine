from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


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
    id: str
    created_at: datetime
    updated_at: datetime
