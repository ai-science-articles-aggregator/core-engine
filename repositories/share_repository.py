from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from domain.models import NotebookShare


class ShareRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ---- read ----

    async def list_for_notebook(self, notebook_id: UUID) -> list[NotebookShare]:
        result = await self.db.execute(
            select(NotebookShare)
            .options(selectinload(NotebookShare.user))
            .where(NotebookShare.notebook_id == notebook_id)
            .order_by(NotebookShare.created_at.asc())
        )
        return list(result.scalars().all())

    async def get(
        self, notebook_id: UUID, user_id: UUID
    ) -> Optional[NotebookShare]:
        result = await self.db.execute(
            select(NotebookShare).where(
                NotebookShare.notebook_id == notebook_id,
                NotebookShare.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_with_user(
        self, notebook_id: UUID, user_id: UUID
    ) -> Optional[NotebookShare]:
        result = await self.db.execute(
            select(NotebookShare)
            .options(
                selectinload(NotebookShare.user),
                selectinload(NotebookShare.area),
            )
            .where(
                NotebookShare.notebook_id == notebook_id,
                NotebookShare.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_shared_notebook_ids_for_user(
        self, user_id: UUID
    ) -> list[UUID]:
        """Список id тетрадей, расшаренных конкретному юзеру."""
        result = await self.db.execute(
            select(NotebookShare.notebook_id).where(NotebookShare.user_id == user_id)
        )
        return [row[0] for row in result.all()]

    async def list_shares_for_user_and_notebooks(
        self, user_id: UUID, notebook_ids: list[UUID]
    ) -> list[NotebookShare]:
        """Батч-фетч share-записей юзера по списку notebook_id, с подгруженной area."""
        if not notebook_ids:
            return []
        result = await self.db.execute(
            select(NotebookShare)
            .options(selectinload(NotebookShare.area))
            .where(
                NotebookShare.user_id == user_id,
                NotebookShare.notebook_id.in_(notebook_ids),
            )
        )
        return list(result.scalars().all())

    # ---- write ----

    async def add(self, share: NotebookShare) -> NotebookShare:
        self.db.add(share)
        await self.db.commit()
        # перезагрузим с user уже подтянутым
        return await self.get_with_user(share.notebook_id, share.user_id)  # type: ignore[return-value]

    async def update_area(
        self, share: NotebookShare, area_id: UUID | None
    ) -> NotebookShare:
        share.area_id = area_id
        await self.db.commit()
        return await self.get_with_user(share.notebook_id, share.user_id)  # type: ignore[return-value]

    async def delete(self, share: NotebookShare) -> None:
        await self.db.delete(share)
        await self.db.commit()
