import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from .area import Area
    from .notebook import Notebook
    from .user import User


class NotebookShare(Base):
    __tablename__ = "notebook_shares"

    notebook_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("notebooks.id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    role: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default="viewer"
    )
    area_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("areas.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    notebook: Mapped["Notebook"] = relationship(back_populates="shares")
    user: Mapped["User"] = relationship(back_populates="notebook_shares")
    area: Mapped[Optional["Area"]] = relationship(back_populates="shares")

    __table_args__ = (
        CheckConstraint(
            "role IN ('viewer', 'commenter', 'editor')",
            name="notebook_shares_role_check",
        ),
        Index("notebook_shares_user_ix", "user_id"),
    )
