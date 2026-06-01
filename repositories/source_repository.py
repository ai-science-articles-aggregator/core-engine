from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.models import NotebookSource


class SourceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_for_notebook(
        self, notebook_id: UUID
    ) -> list[NotebookSource]:
        result = await self.db.execute(
            select(NotebookSource)
            .where(NotebookSource.notebook_id == notebook_id)
            .order_by(NotebookSource.added_at.asc())
        )
        return list(result.scalars().all())

    async def get(
        self, notebook_id: UUID, article_id: str
    ) -> Optional[NotebookSource]:
        result = await self.db.execute(
            select(NotebookSource).where(
                NotebookSource.notebook_id == notebook_id,
                NotebookSource.article_id == article_id,
            )
        )
        return result.scalar_one_or_none()

    async def existing_source_article_ids(
        self, notebook_id: UUID, article_ids: list[str]
    ) -> set[str]:
        if not article_ids:
            return set()
        result = await self.db.execute(
            select(NotebookSource.article_id).where(
                NotebookSource.notebook_id == notebook_id,
                NotebookSource.article_id.in_(article_ids),
            )
        )
        return {row[0] for row in result.all()}

    async def bulk_add(
        self, notebook_id: UUID, article_ids: list[str]
    ) -> None:
        for aid in article_ids:
            self.db.add(NotebookSource(notebook_id=notebook_id, article_id=aid))
        await self.db.commit()

    async def update_selected(
        self, source: NotebookSource, selected: bool
    ) -> NotebookSource:
        source.selected = selected
        await self.db.commit()
        return await self.get(source.notebook_id, source.article_id)  # type: ignore[return-value]

    async def delete(self, source: NotebookSource) -> None:
        await self.db.delete(source)
        await self.db.commit()
