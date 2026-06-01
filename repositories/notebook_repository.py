from typing import Literal, Optional
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from domain.models import (
    Notebook,
    NotebookNote,
    NotebookShare,
    NotebookSource,
    NotebookTag,
    Tag,
)


class NotebookRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ---- внутреннее ----

    def _base_select(self):
        """SELECT с eager-load для связей, необходимых в response."""
        return select(Notebook).options(
            selectinload(Notebook.area),
            selectinload(Notebook.tags),
            selectinload(Notebook.user),
        )

    async def _counts(self, notebook_id: UUID) -> tuple[int, int]:
        sources = await self.db.scalar(
            select(func.count())
            .select_from(NotebookSource)
            .where(NotebookSource.notebook_id == notebook_id)
        )
        notes = await self.db.scalar(
            select(func.count())
            .select_from(NotebookNote)
            .where(NotebookNote.notebook_id == notebook_id)
        )
        return int(sources or 0), int(notes or 0)

    # ---- public API ----

    async def create_notebook(self, notebook: Notebook) -> Notebook:
        self.db.add(notebook)
        await self.db.commit()
        # re-fetch через base_select, чтобы получить eager-loaded area
        # (db.refresh с attribute_names=["area"] под async падает с MissingGreenlet)
        refreshed = await self.get_notebook(notebook.id)
        assert refreshed is not None
        return refreshed

    async def get_notebook(self, notebook_id: UUID) -> Optional[Notebook]:
        result = await self.db.execute(
            self._base_select().where(Notebook.id == notebook_id)
        )
        return result.scalar_one_or_none()

    async def list_for_viewer(
        self,
        viewer_id: UUID,
        *,
        owned_only: bool = False,
        shared_only: bool = False,
        visibility: str | None = None,
        area_id: UUID | None = None,
        q: str | None = None,
        tag_slugs: list[str] | None = None,
        tags_op: Literal["and", "or"] = "and",
    ) -> list[Notebook]:
        """owned + shared с произвольной комбинацией фильтров.

        - owned_only: только мои тетради
        - shared_only: только расшаренные мне
        - оба False: и то, и то (объединение)
        """
        stmt = self._base_select()

        shared_ids_subq = (
            select(NotebookShare.notebook_id)
            .where(NotebookShare.user_id == viewer_id)
            .scalar_subquery()
        )

        if owned_only and shared_only:
            # бессмысленная комбинация — вернём пусто
            return []
        if owned_only:
            stmt = stmt.where(Notebook.user_id == viewer_id)
        elif shared_only:
            stmt = stmt.where(Notebook.id.in_(shared_ids_subq))
        else:
            stmt = stmt.where(
                or_(
                    Notebook.user_id == viewer_id,
                    Notebook.id.in_(shared_ids_subq),
                )
            )

        if visibility:
            stmt = stmt.where(Notebook.visibility == visibility)

        if area_id is not None:
            stmt = stmt.where(Notebook.area_id == area_id)

        if q:
            pattern = f"%{q}%"
            stmt = stmt.where(
                or_(
                    Notebook.name.ilike(pattern),
                    Notebook.description.ilike(pattern),
                )
            )

        if tag_slugs:
            if tags_op == "or":
                stmt = (
                    stmt.join(NotebookTag, NotebookTag.notebook_id == Notebook.id)
                    .join(Tag, Tag.id == NotebookTag.tag_id)
                    .where(Tag.slug.in_(tag_slugs))
                    .distinct()
                )
            else:  # and
                for slug in tag_slugs:
                    sub = (
                        select(1)
                        .select_from(NotebookTag)
                        .join(Tag, Tag.id == NotebookTag.tag_id)
                        .where(
                            NotebookTag.notebook_id == Notebook.id,
                            Tag.slug == slug,
                        )
                    )
                    stmt = stmt.where(sub.exists())

        stmt = stmt.order_by(Notebook.updated_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # Legacy-обёртка: для обратной совместимости со старыми внутренними вызовами
    async def get_notebooks_by_user(
        self, user_id: UUID, **kwargs
    ) -> list[Notebook]:
        return await self.list_for_viewer(user_id, owned_only=True, **kwargs)

    async def counts_for(self, notebook_id: UUID) -> tuple[int, int]:
        """Возвращает (sources_count, notes_count) для одной тетради."""
        return await self._counts(notebook_id)

    async def update_notebook(
        self,
        notebook_id: UUID,
        *,
        name: str | None = None,
        description: str | None = None,
        area_id: UUID | None = None,
        visibility: str | None = None,
        clear_area: bool = False,
        tags: list | None = None,  # None = не трогать, [] = очистить
    ) -> Optional[Notebook]:
        notebook = await self.get_notebook(notebook_id)
        if not notebook:
            return None
        if name is not None:
            notebook.name = name
        if description is not None:
            notebook.description = description
        if clear_area:
            notebook.area_id = None
        elif area_id is not None:
            notebook.area_id = area_id
        if visibility is not None:
            notebook.visibility = visibility
        if tags is not None:
            notebook.tags = tags
        await self.db.commit()
        return await self.get_notebook(notebook_id)

    async def delete_notebook(self, notebook_id: UUID) -> bool:
        notebook = await self.db.get(Notebook, notebook_id)
        if not notebook:
            return False
        await self.db.delete(notebook)
        await self.db.commit()
        return True

