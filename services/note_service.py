from uuid import UUID

from fastapi import HTTPException, status

from domain.models import Notebook, NotebookNote
from domain.schemas.notes import NoteCreate, NoteRead, NoteUpdate
from repositories import NoteRepository


class NoteService:
    def __init__(self, repository: NoteRepository):
        self.repository = repository

    async def list_for_notebook(self, notebook_id: UUID) -> list[NoteRead]:
        notes = await self.repository.list_for_notebook(notebook_id)
        return [NoteRead.model_validate(n) for n in notes]

    async def create(
        self, notebook: Notebook, current_user_id: UUID, payload: NoteCreate
    ) -> NoteRead:
        note = NotebookNote(
            notebook_id=notebook.id,
            user_id=current_user_id,
            title=payload.title,
            body=payload.body,
        )
        note = await self.repository.add(note)
        return NoteRead.model_validate(note)

    async def update(
        self,
        notebook: Notebook,
        note_id: UUID,
        current_user_id: UUID,
        role: str,
        payload: NoteUpdate,
    ) -> NoteRead:
        note = await self.repository.get(note_id)
        if not note or note.notebook_id != notebook.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Note not found"
            )
        # автор записи или owner могут править
        if note.user_id != current_user_id and role != "owner":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the author or owner can edit this note",
            )
        updated = await self.repository.update(note, title=payload.title, body=payload.body)
        return NoteRead.model_validate(updated)

    async def delete(
        self,
        notebook: Notebook,
        note_id: UUID,
        current_user_id: UUID,
        role: str,
    ) -> None:
        note = await self.repository.get(note_id)
        if not note or note.notebook_id != notebook.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Note not found"
            )
        if note.user_id != current_user_id and role != "owner":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the author or owner can delete this note",
            )
        await self.repository.delete(note)
