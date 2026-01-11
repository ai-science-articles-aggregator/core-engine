from fastapi import APIRouter, Depends

from core.auth import security
from dependecies import get_notebooks_service
from services import NotebookService

router = APIRouter(
    prefix="/notebooks",
    tags=["notebooks"],
    dependencies=[Depends(security.access_token_required)],
)


@router.get("/")
async def get_notebooks():
    return {"message": "Get notebooks"}


@router.get("/{notebook_id}")
async def get_notebook(notebook_id: str):
    return {"message": "Get notebooks"}


@router.post("/create")
async def create_notebook(service: NotebookService = Depends(get_notebooks_service)):
    notebook = await service.create_notebook()

    return notebook
