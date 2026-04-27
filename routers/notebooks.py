import json
import os
import sys
from uuid import UUID

import grpc
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core.auth import security
from dependecies import (
    get_notebooks_service,
    get_rag_stub,
    get_summary_stub,
)
from domain.schemas import (
    ArticleResult,
    NotebookCreate,
    NotebookResponse,
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


@router.get("/", response_model=list[NotebookResponse])
async def get_notebooks(
    payload=Depends(security.access_token_required),
    service: NotebookService = Depends(get_notebooks_service),
):
    user_id = UUID(payload.sub)
    notebooks = await service.repository.get_notebooks_by_user(user_id)
    return [NotebookResponse.model_validate(nb) for nb in notebooks]


@router.get("/{notebook_id}", response_model=NotebookResponse)
async def get_notebook(
    notebook_id: UUID,
    payload=Depends(security.access_token_required),
    service: NotebookService = Depends(get_notebooks_service),
):
    notebook = await service.repository.get_notebook(notebook_id)

    if not notebook:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Notebook not found")

    # Проверка: ноутбук принадлежит пользователю
    if notebook.user_id != UUID(payload.sub):
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="Access denied")

    return NotebookResponse.model_validate(notebook)


@router.post("/create", response_model=NotebookResponse)
async def create_notebook(
    data: NotebookCreate,
    payload=Depends(security.access_token_required),
    service: NotebookService = Depends(get_notebooks_service),
):
    user_id = UUID(payload.sub)

    notebook = await service.create_notebook(
        user_id=user_id, name=data.name, description=data.description
    )

    return notebook


@router.put("/{notebook_id}", response_model=NotebookResponse)
async def update_notebook(
    notebook_id: UUID,
    data: NotebookCreate,
    payload=Depends(security.access_token_required),
    service: NotebookService = Depends(get_notebooks_service),
):
    user_id = UUID(payload.sub)
    notebook = await service.repository.get_notebook(notebook_id)

    if not notebook:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Notebook not found")

    if notebook.user_id != user_id:
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="Access denied")

    updated = await service.repository.update_notebook(
        notebook_id=notebook_id, name=data.name, description=data.description
    )

    return NotebookResponse.model_validate(updated)


@router.delete("/{notebook_id}", response_model=StatusResponse)
async def delete_notebook(
    notebook_id: UUID,
    payload=Depends(security.access_token_required),
    service: NotebookService = Depends(get_notebooks_service),
):
    user_id = UUID(payload.sub)
    notebook = await service.repository.get_notebook(notebook_id)

    if not notebook:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Notebook not found")

    if notebook.user_id != user_id:
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="Access denied")

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
    notebook = await service.repository.get_notebook(notebook_id)
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")
    if notebook.user_id != UUID(payload.sub):
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        response = await rag_stub.Search(
            rag_pb2.SearchRequest(
                query=data.query,
                top_k=data.top_k,
            )
        )
    except grpc.aio.AioRpcError as e:
        raise HTTPException(
            status_code=503, detail=f"RAG service unavailable: {e.details()}"
        )

    articles = [
        ArticleResult(
            id=a.id,
            title=a.title,
            authors=a.authors,
            score=a.score,
        )
        for a in response.articles
    ]

    await service.save_search_results(
        notebook_id=notebook_id,
        query=data.query,
        articles=articles,
    )

    return SearchResponse(query=data.query, articles=articles)


@router.post("/{notebook_id}/summarize")
async def summarize_articles(
    notebook_id: UUID,
    data: SummarizeRequest,
    payload=Depends(security.access_token_required),
    service: NotebookService = Depends(get_notebooks_service),
    summary_stub: summary_pb2_grpc.SummaryServiceStub = Depends(get_summary_stub),
):
    notebook = await service.repository.get_notebook(notebook_id)
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")
    if notebook.user_id != UUID(payload.sub):
        raise HTTPException(status_code=403, detail="Access denied")

    async def event_stream():
        try:
            async for response in summary_stub.Summarize(
                summary_pb2.SummarizeRequest(
                    article_ids=data.article_ids,
                    query=data.query,
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
