import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, ForeignKey, Index, String, func, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from .notebook import Notebook
    from .notebook_share import NotebookShare
    from .user import User


class Area(Base):
    __tablename__ = "areas"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    palette_key: Mapped[str] = mapped_column(
        String(16), nullable=False, default="sienna"
    )
    archived_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="areas")
    notebooks: Mapped[List["Notebook"]] = relationship(back_populates="area")
    shares: Mapped[List["NotebookShare"]] = relationship(back_populates="area")

    __table_args__ = (
        Index(
            "areas_user_slug_active_uq",
            "user_id",
            "slug",
            unique=True,
            postgresql_where=text("archived_at IS NULL"),
        ),
        Index(
            "areas_user_active_ix",
            "user_id",
            postgresql_where=text("archived_at IS NULL"),
        ),
    )

    def __repr__(self) -> str:
        return f"<Area {self.slug} user={self.user_id}>"
