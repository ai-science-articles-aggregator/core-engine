from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from core.auth import security
from dependecies import get_notebooks_service
from domain.schemas import NotebookCreate, NotebookResponse
from services import NotebookService

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
        user_id=user_id,
        name=data.name,
        description=data.description
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
        notebook_id=notebook_id,
        name=data.name,
        description=data.description
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
