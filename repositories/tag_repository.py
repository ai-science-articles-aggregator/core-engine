from typing import Optional
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.models import NotebookTag, Tag


class TagRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ---- read ----

    async def get(self, tag_id: UUID) -> Optional[Tag]:
        return await self.db.get(Tag, tag_id)

    async def get_for_user(self, tag_id: UUID, user_id: UUID) -> Optional[Tag]:
        result = await self.db.execute(
            select(Tag).where(Tag.id == tag_id, Tag.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, user_id: UUID, slug: str) -> Optional[Tag]:
        result = await self.db.execute(
            select(Tag).where(Tag.user_id == user_id, Tag.slug == slug)
        )
        return result.scalar_one_or_none()

    async def get_by_slugs(
        self, user_id: UUID, slugs: list[str]
    ) -> list[Tag]:
        if not slugs:
            return []
        result = await self.db.execute(
            select(Tag).where(Tag.user_id == user_id, Tag.slug.in_(slugs))
        )
        return list(result.scalars().all())

    async def list_with_counts(
        self, user_id: UUID
    ) -> list[tuple[Tag, int]]:
        """Все теги юзера с числом тетрадей, к которым они привязаны."""
        stmt = (
            select(Tag, func.count(NotebookTag.notebook_id).label("notebook_count"))
            .outerjoin(NotebookTag, NotebookTag.tag_id == Tag.id)
            .where(Tag.user_id == user_id)
            .group_by(Tag.id)
            .order_by(Tag.name.asc())
        )
        result = await self.db.execute(stmt)
        return [(row[0], int(row[1])) for row in result.all()]

    async def search(
        self, user_id: UUID, query: str, limit: int = 10
    ) -> list[Tag]:
        """Autocomplete: prefix-match по slug или name (ILIKE)."""
        q = query.strip().lower()
        if not q:
            return []
        pattern = f"{q}%"
        result = await self.db.execute(
            select(Tag)
            .where(
                Tag.user_id == user_id,
                or_(
                    Tag.slug.ilike(pattern),
                    Tag.name.ilike(pattern),
                ),
            )
            .order_by(Tag.name.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    # ---- write ----

    async def add(self, tag: Tag, *, commit: bool = False) -> Tag:
        self.db.add(tag)
        if commit:
            await self.db.commit()
            await self.db.refresh(tag)
        else:
            await self.db.flush()
        return tag

    async def update_name_slug(
        self, tag: Tag, *, name: str, slug: str, commit: bool = True
    ) -> Tag:
        tag.name = name
        tag.slug = slug
        if commit:
            await self.db.commit()
            await self.db.refresh(tag)
        return tag

    async def delete(self, tag: Tag) -> None:
        await self.db.delete(tag)
        await self.db.commit()
