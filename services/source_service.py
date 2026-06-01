from uuid import UUID

from fastapi import HTTPException, status

from domain.schemas.sources import SourceCreate, SourceRead
from repositories import SourceRepository


class SourceService:
    def __init__(self, repository: SourceRepository):
        self.repository = repository

    async def list_for_notebook(self, notebook_id: UUID) -> list[SourceRead]:
        sources = await self.repository.list_for_notebook(notebook_id)
        return [SourceRead.model_validate(s) for s in sources]

    async def add_sources(
        self, notebook_id: UUID, payload: SourceCreate
    ) -> list[SourceRead]:
        # дедуп — что уже привязано
        existing_links = await self.repository.existing_source_article_ids(
            notebook_id, payload.article_ids
        )
        # сохраняем порядок прихода
        seen: set[str] = set()
        to_add: list[str] = []
        for aid in payload.article_ids:
            if aid in existing_links or aid in seen:
                continue
            seen.add(aid)
            to_add.append(aid)
        if to_add:
            await self.repository.bulk_add(notebook_id, to_add)
        return await self.list_for_notebook(notebook_id)

    async def toggle_selected(
        self, notebook_id: UUID, article_id: str, selected: bool
    ) -> SourceRead:
        source = await self.repository.get(notebook_id, article_id)
        if not source:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Source not found"
            )
        updated = await self.repository.update_selected(source, selected)
        return SourceRead.model_validate(updated)

    async def remove(self, notebook_id: UUID, article_id: str) -> None:
        source = await self.repository.get(notebook_id, article_id)
        if not source:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Source not found"
            )
        await self.repository.delete(source)
