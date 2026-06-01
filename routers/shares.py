from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from core.auth import security
from dependecies import get_notebooks_service, get_share_service
from domain.schemas.share import ShareCreate, ShareRead, ShareUpdateMe
from services import NotebookService, ShareService

router = APIRouter(
    prefix="/notebooks/{notebook_id}/shares",
    tags=["shares"],
    dependencies=[Depends(security.access_token_required)],
)


async def _load_notebook(
    notebook_id: UUID, notebook_service: NotebookService
):
    notebook = await notebook_service.repository.get_notebook(notebook_id)
    if not notebook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notebook not found"
        )
    return notebook


@router.get("", response_model=list[ShareRead])
async def list_shares(
    notebook_id: UUID,
    payload=Depends(security.access_token_required),
    notebook_service: NotebookService = Depends(get_notebooks_service),
    share_service: ShareService = Depends(get_share_service),
):
    user_id = UUID(payload.sub)
    notebook = await _load_notebook(notebook_id, notebook_service)
    return await share_service.list_for_notebook(notebook, user_id)


@router.post("", response_model=ShareRead, status_code=status.HTTP_201_CREATED)
async def create_share(
    notebook_id: UUID,
    data: ShareCreate,
    payload=Depends(security.access_token_required),
    notebook_service: NotebookService = Depends(get_notebooks_service),
    share_service: ShareService = Depends(get_share_service),
):
    user_id = UUID(payload.sub)
    notebook = await _load_notebook(notebook_id, notebook_service)
    return await share_service.create_share(notebook, user_id, data)


@router.patch("/me", response_model=ShareRead)
async def update_my_share(
    notebook_id: UUID,
    data: ShareUpdateMe,
    payload=Depends(security.access_token_required),
    notebook_service: NotebookService = Depends(get_notebooks_service),
    share_service: ShareService = Depends(get_share_service),
):
    user_id = UUID(payload.sub)
    notebook = await _load_notebook(notebook_id, notebook_service)
    return await share_service.update_my_share(notebook, user_id, data)


@router.delete(
    "/{recipient_user_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def revoke_share(
    notebook_id: UUID,
    recipient_user_id: UUID,
    payload=Depends(security.access_token_required),
    notebook_service: NotebookService = Depends(get_notebooks_service),
    share_service: ShareService = Depends(get_share_service),
):
    user_id = UUID(payload.sub)
    notebook = await _load_notebook(notebook_id, notebook_service)
    await share_service.revoke(notebook, user_id, recipient_user_id)
