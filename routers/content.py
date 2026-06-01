from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from core.auth import security
from dependecies import (
    get_message_service,
    get_note_service,
    get_notebooks_service,
    get_source_service,
    get_summary_stub,
)
from domain.schemas.messages import ChatMessageCreate, ChatMessageRead
from domain.schemas.notes import NoteCreate, NoteRead, NoteUpdate
from domain.schemas.sources import SourceCreate, SourceRead, SourceToggle
from services import MessageService, NotebookService, NoteService, SourceService

router = APIRouter(
    prefix="/notebooks/{notebook_id}",
    tags=["content"],
    dependencies=[Depends(security.access_token_required)],
)


async def _resolve_with_role(
    service: NotebookService, notebook_id: UUID, user_id: UUID
):
    notebook = await service.repository.get_notebook(notebook_id)
    if not notebook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notebook not found"
        )
    role = await service.get_role(notebook, user_id)
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    return notebook, role


def _require_role(role: str, allowed: set[str], action: str) -> None:
    if role not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{role}' cannot {action}",
        )


WRITE_ROLES = {"owner", "editor"}
COMMENT_ROLES = {"owner", "editor", "commenter"}
READ_ROLES = {"owner", "editor", "commenter", "viewer"}


@router.get("/sources", response_model=list[SourceRead])
async def list_sources(
    notebook_id: UUID,
    payload=Depends(security.access_token_required),
    nb_service: NotebookService = Depends(get_notebooks_service),
    service: SourceService = Depends(get_source_service),
):
    user_id = UUID(payload.sub)
    _, role = await _resolve_with_role(nb_service, notebook_id, user_id)
    _require_role(role, READ_ROLES, "view sources")
    return await service.list_for_notebook(notebook_id)


@router.post(
    "/sources", response_model=list[SourceRead], status_code=status.HTTP_201_CREATED
)
async def add_sources(
    notebook_id: UUID,
    data: SourceCreate,
    payload=Depends(security.access_token_required),
    nb_service: NotebookService = Depends(get_notebooks_service),
    service: SourceService = Depends(get_source_service),
):
    user_id = UUID(payload.sub)
    _, role = await _resolve_with_role(nb_service, notebook_id, user_id)
    _require_role(role, WRITE_ROLES, "add sources")
    return await service.add_sources(notebook_id, data)


@router.patch("/sources/{article_id}", response_model=SourceRead)
async def toggle_source(
    notebook_id: UUID,
    article_id: str,
    data: SourceToggle,
    payload=Depends(security.access_token_required),
    nb_service: NotebookService = Depends(get_notebooks_service),
    service: SourceService = Depends(get_source_service),
):
    user_id = UUID(payload.sub)
    _, role = await _resolve_with_role(nb_service, notebook_id, user_id)
    _require_role(role, WRITE_ROLES, "toggle source selection")
    return await service.toggle_selected(notebook_id, article_id, data.selected)


@router.delete("/sources/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_source(
    notebook_id: UUID,
    article_id: str,
    payload=Depends(security.access_token_required),
    nb_service: NotebookService = Depends(get_notebooks_service),
    service: SourceService = Depends(get_source_service),
):
    user_id = UUID(payload.sub)
    _, role = await _resolve_with_role(nb_service, notebook_id, user_id)
    _require_role(role, WRITE_ROLES, "remove sources")
    await service.remove(notebook_id, article_id)


# ---- notes ----------------------------------------------------------------


@router.get("/notes", response_model=list[NoteRead])
async def list_notes(
    notebook_id: UUID,
    payload=Depends(security.access_token_required),
    nb_service: NotebookService = Depends(get_notebooks_service),
    service: NoteService = Depends(get_note_service),
):
    user_id = UUID(payload.sub)
    _, role = await _resolve_with_role(nb_service, notebook_id, user_id)
    _require_role(role, READ_ROLES, "view notes")
    return await service.list_for_notebook(notebook_id)


@router.post("/notes", response_model=NoteRead, status_code=status.HTTP_201_CREATED)
async def create_note(
    notebook_id: UUID,
    data: NoteCreate,
    payload=Depends(security.access_token_required),
    nb_service: NotebookService = Depends(get_notebooks_service),
    service: NoteService = Depends(get_note_service),
):
    user_id = UUID(payload.sub)
    notebook, role = await _resolve_with_role(nb_service, notebook_id, user_id)
    _require_role(role, COMMENT_ROLES, "create notes")
    return await service.create(notebook, user_id, data)


@router.patch("/notes/{note_id}", response_model=NoteRead)
async def update_note(
    notebook_id: UUID,
    note_id: UUID,
    data: NoteUpdate,
    payload=Depends(security.access_token_required),
    nb_service: NotebookService = Depends(get_notebooks_service),
    service: NoteService = Depends(get_note_service),
):
    user_id = UUID(payload.sub)
    notebook, role = await _resolve_with_role(nb_service, notebook_id, user_id)
    _require_role(role, COMMENT_ROLES, "edit notes")
    return await service.update(notebook, note_id, user_id, role, data)


@router.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    notebook_id: UUID,
    note_id: UUID,
    payload=Depends(security.access_token_required),
    nb_service: NotebookService = Depends(get_notebooks_service),
    service: NoteService = Depends(get_note_service),
):
    user_id = UUID(payload.sub)
    notebook, role = await _resolve_with_role(nb_service, notebook_id, user_id)
    _require_role(role, COMMENT_ROLES, "delete notes")
    await service.delete(notebook, note_id, user_id, role)


# ---- chat -----------------------------------------------------------------


@router.get("/messages", response_model=list[ChatMessageRead])
async def list_messages(
    notebook_id: UUID,
    payload=Depends(security.access_token_required),
    nb_service: NotebookService = Depends(get_notebooks_service),
    service: MessageService = Depends(get_message_service),
):
    user_id = UUID(payload.sub)
    _, role = await _resolve_with_role(nb_service, notebook_id, user_id)
    _require_role(role, READ_ROLES, "view messages")
    return await service.list_for_notebook(notebook_id)


@router.post("/messages")
async def post_message(
    notebook_id: UUID,
    data: ChatMessageCreate,
    payload=Depends(security.access_token_required),
    nb_service: NotebookService = Depends(get_notebooks_service),
    service: MessageService = Depends(get_message_service),
    summary_stub=Depends(get_summary_stub),
):
    user_id = UUID(payload.sub)
    _, role = await _resolve_with_role(nb_service, notebook_id, user_id)
    _require_role(role, COMMENT_ROLES, "post messages")

    # 1. persist user message (sync)
    await service.post_user_message(notebook_id, data)

    # 2. SSE stream + persist assistant message in background
    return StreamingResponse(
        service.stream_assistant_reply(notebook_id, data.text, summary_stub),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
