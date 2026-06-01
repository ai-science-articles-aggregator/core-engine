import json
import os
import sys
from typing import Literal, Optional
from uuid import UUID

import grpc
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core.auth import security
from core.utils.slug import slugify
from dependecies import (
    get_notebooks_service,
    get_rag_stub,
    get_summary_stub,
)
from domain.schemas import (
    ArticleResult,
    NotebookCreate,
    NotebookListItem,
    SearchRequest,
    SearchResponse,
    SummarizeRequest,
)
from services import NotebookService

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "generated"))

from rag.v1 import rag_pb2, rag_pb2_grpc
from summary.v1 import summary_pb2, summary_pb2_grpc

router = APIRouter(
    prefix="/notebooks",
    tags=["notebooks"],
    dependencies=[Depends(security.access_token_required)],
)


class StatusResponse(BaseModel):
    status: str
    message: str


# ---- helpers -------------------------------------------------------------

async def _resolve_with_role(
    service: NotebookService, notebook_id: UUID, user_id: UUID
):
    """Возвращает (notebook, role). 404 если нет тетради, 403 если нет доступа."""
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


def _require_role(role: str | None, allowed: set[str], action: str) -> None:
    if role not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{role}' cannot {action}",
        )


# ---- endpoints -----------------------------------------------------------

@router.get("/", response_model=list[NotebookListItem])
async def get_notebooks(
    owned_only: bool = Query(default=False),
    shared_only: bool = Query(default=False),
    visibility: Optional[Literal["private", "shared", "public"]] = Query(default=None),
    area_id: Optional[UUID] = Query(default=None),
    q: Optional[str] = Query(default=None, max_length=200),
    tags: Optional[str] = Query(default=None),
    tags_op: Literal["and", "or"] = Query(default="and"),
    payload=Depends(security.access_token_required),
    service: NotebookService = Depends(get_notebooks_service),
):
    user_id = UUID(payload.sub)
    tag_slugs: Optional[list[str]] = None
    if tags:
        tag_slugs = [s for s in (slugify(t) for t in tags.split(",")) if s]
        if not tag_slugs:
            tag_slugs = None
    return await service.list_notebooks(
        user_id,
        owned_only=owned_only,
        shared_only=shared_only,
        visibility=visibility,
        area_id=area_id,
        q=q,
        tag_slugs=tag_slugs,
        tags_op=tags_op,
    )


@router.get("/{notebook_id}", response_model=NotebookListItem)
async def get_notebook(
    notebook_id: UUID,
    payload=Depends(security.access_token_required),
    service: NotebookService = Depends(get_notebooks_service),
):
    user_id = UUID(payload.sub)
    item = await service.get_notebook(notebook_id, user_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notebook not found"
        )
    return item


@router.post("/create", response_model=NotebookListItem, status_code=status.HTTP_201_CREATED)
async def create_notebook(
    data: NotebookCreate,
    payload=Depends(security.access_token_required),
    service: NotebookService = Depends(get_notebooks_service),
):
    user_id = UUID(payload.sub)
    return await service.create_notebook(user_id=user_id, payload=data)


@router.put("/{notebook_id}", response_model=NotebookListItem)
async def update_notebook(
    notebook_id: UUID,
    data: NotebookCreate,
    payload=Depends(security.access_token_required),
    service: NotebookService = Depends(get_notebooks_service),
):
    user_id = UUID(payload.sub)
    _, role = await _resolve_with_role(service, notebook_id, user_id)
    _require_role(role, {"owner", "editor"}, "edit this notebook")
    updated = await service.update_notebook(notebook_id, user_id, data)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notebook not found"
        )
    return updated


@router.delete("/{notebook_id}", response_model=StatusResponse)
async def delete_notebook(
    notebook_id: UUID,
    payload=Depends(security.access_token_required),
    service: NotebookService = Depends(get_notebooks_service),
):
    user_id = UUID(payload.sub)
    _, role = await _resolve_with_role(service, notebook_id, user_id)
    _require_role(role, {"owner"}, "delete this notebook")
    await service.repository.delete_notebook(notebook_id)
    return StatusResponse(status="success", message="Notebook deleted")


@router.post("/{notebook_id}/search", response_model=SearchResponse)
async def search_articles(
    notebook_id: UUID,
    data: SearchRequest,
    payload=Depends(security.access_token_required),
    service: NotebookService = Depends(get_notebooks_service),
    rag_stub: rag_pb2_grpc.RAGServiceStub = Depends(get_rag_stub),
):
    user_id = UUID(payload.sub)
    _, role = await _resolve_with_role(service, notebook_id, user_id)
    # search доступен любому с доступом (включая viewer)
    _require_role(role, {"owner", "viewer", "commenter", "editor"}, "search in this notebook")

    try:
        response = await rag_stub.Search(
            rag_pb2.SearchRequest(query=data.query, top_k=data.top_k)
        )
    except grpc.aio.AioRpcError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"RAG service unavailable: {e.details()}",
        )

    articles = [
        ArticleResult(id=a.id, title=a.title, authors=a.authors, score=a.score)
        for a in response.articles
    ]
    # NB: ничего у себя не сохраняем — статьи живут в RAG-овой БД.
    # Пользователь выбирает что добавить через POST /notebooks/:id/sources.
    return SearchResponse(query=data.query, articles=articles)


@router.post("/{notebook_id}/summarize")
async def summarize_articles(
    notebook_id: UUID,
    data: SummarizeRequest,
    payload=Depends(security.access_token_required),
    service: NotebookService = Depends(get_notebooks_service),
    summary_stub: summary_pb2_grpc.SummaryServiceStub = Depends(get_summary_stub),
):
    user_id = UUID(payload.sub)
    _, role = await _resolve_with_role(service, notebook_id, user_id)
    _require_role(role, {"owner", "viewer", "commenter", "editor"}, "summarize")

    async def event_stream():
        try:
            async for response in summary_stub.Summarize(
                summary_pb2.SummarizeRequest(
                    article_ids=data.article_ids, query=data.query
                )
            ):
                payload_data = json.dumps({"token": response.token})
                yield f"data: {payload_data}\n\n"
        except grpc.aio.AioRpcError as e:
            error = json.dumps({"error": e.details()})
            yield f"data: {error}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
