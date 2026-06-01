from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from domain.models import Area


class AreaRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ---- read ----

    async def list_active_for_user(self, user_id: UUID) -> list[Area]:
        result = await self.db.execute(
            select(Area)
            .where(Area.user_id == user_id, Area.archived_at.is_(None))
            .order_by(Area.created_at.asc())
        )
        return list(result.scalars().all())

    async def get(self, area_id: UUID) -> Optional[Area]:
        return await self.db.get(Area, area_id)

    async def get_active_for_user(
        self, area_id: UUID, user_id: UUID
    ) -> Optional[Area]:
        result = await self.db.execute(
            select(Area).where(
                Area.id == area_id,
                Area.user_id == user_id,
                Area.archived_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, user_id: UUID, slug: str) -> Optional[Area]:
        """Активная область с таким slug у юзера, либо None."""
        result = await self.db.execute(
            select(Area).where(
                Area.user_id == user_id,
                Area.slug == slug,
                Area.archived_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    # ---- write ----

    async def add(self, area: Area, *, commit: bool = True) -> Area:
        self.db.add(area)
        if commit:
            await self.db.commit()
            await self.db.refresh(area)
        else:
            await self.db.flush()
        return area

    async def bulk_add(self, areas: list[Area]) -> list[Area]:
        """Сидинг при регистрации — без commit, чтобы лежать в одной транзакции."""
        for a in areas:
            self.db.add(a)
        await self.db.flush()
        return areas

    async def update(
        self,
        area: Area,
        *,
        name: str | None = None,
        slug: str | None = None,
        palette_key: str | None = None,
    ) -> Area:
        if name is not None:
            area.name = name
        if slug is not None:
            area.slug = slug
        if palette_key is not None:
            area.palette_key = palette_key
        await self.db.commit()
        await self.db.refresh(area)
        return area

    async def soft_delete(self, area: Area) -> Area:
        area.archived_at = func.now()
        await self.db.commit()
        await self.db.refresh(area)
        return area
