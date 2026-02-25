import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from .notebook import Notebook


class File(Base):
    __tablename__ = "files"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), default=uuid.uuid4, primary_key=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Связь с ноутбуком
    notebook_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("notebooks.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    upload_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Отношения
    notebook: Mapped["Notebook"] = relationship(back_populates="files")
