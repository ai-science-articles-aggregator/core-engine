import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from .notebook import Notebook


class NotebookSource(Base):
    """Связка тетради и id статьи (из внешней RAG БД).

    Хранит только идентификатор и `selected`-флаг. Метаданные статьи
    (title, authors, abstract, ...) живут в RAG и не дублируются у нас.
    """

    __tablename__ = "notebook_sources"

    notebook_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("notebooks.id", ondelete="CASCADE"),
        primary_key=True,
    )
    # text-id из RAG (article.id). Не UUID, не FK — статьи у нас не хранятся.
    article_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    selected: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    notebook: Mapped["Notebook"] = relationship(back_populates="sources")
