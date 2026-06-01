import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from .area import Area
    from .file import File
    from .notebook_chat_message import NotebookChatMessage
    from .notebook_note import NotebookNote
    from .notebook_share import NotebookShare
    from .notebook_source import NotebookSource
    from .tag import Tag
    from .user import User


class Notebook(Base):
    __tablename__ = "notebooks"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), default=uuid.uuid4, primary_key=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    area_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("areas.id", ondelete="SET NULL"),
        nullable=True,
    )
    visibility: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default="private"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="notebooks")
    area: Mapped[Optional["Area"]] = relationship(back_populates="notebooks")
    files: Mapped[List["File"]] = relationship(
        back_populates="notebook", cascade="all, delete-orphan"
    )
    tags: Mapped[List["Tag"]] = relationship(
        secondary="notebook_tags", back_populates="notebooks"
    )
    shares: Mapped[List["NotebookShare"]] = relationship(
        back_populates="notebook", cascade="all, delete-orphan"
    )
    sources: Mapped[List["NotebookSource"]] = relationship(
        back_populates="notebook", cascade="all, delete-orphan"
    )
    chat_messages: Mapped[List["NotebookChatMessage"]] = relationship(
        back_populates="notebook", cascade="all, delete-orphan"
    )
    notes: Mapped[List["NotebookNote"]] = relationship(
        back_populates="notebook", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "visibility IN ('private', 'shared', 'public')",
            name="notebooks_visibility_check",
        ),
    )
