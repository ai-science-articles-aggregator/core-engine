from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.models import NotebookNote


class NoteRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_for_notebook(self, notebook_id: UUID) -> list[NotebookNote]:
        result = await self.db.execute(
            select(NotebookNote)
            .where(NotebookNote.notebook_id == notebook_id)
            .order_by(NotebookNote.updated_at.desc())
        )
        return list(result.scalars().all())

    async def get(self, note_id: UUID) -> Optional[NotebookNote]:
        return await self.db.get(NotebookNote, note_id)

    async def add(self, note: NotebookNote) -> NotebookNote:
        self.db.add(note)
        await self.db.commit()
        await self.db.refresh(note)
        return note

    async def update(
        self,
        note: NotebookNote,
        *,
        title: Optional[str] = None,
        body: Optional[str] = None,
    ) -> NotebookNote:
        if title is not None:
            note.title = title
        if body is not None:
            note.body = body
        await self.db.commit()
        await self.db.refresh(note)
        return note

    async def delete(self, note: NotebookNote) -> None:
        await self.db.delete(note)
        await self.db.commit()
