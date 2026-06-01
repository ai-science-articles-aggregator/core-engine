from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from core.auth import security
from dependecies import get_tag_service
from domain.schemas.tag import TagRename, TagShort, TagWithCount
from services import TagService

router = APIRouter(
    prefix="/tags",
    tags=["tags"],
    dependencies=[Depends(security.access_token_required)],
)


@router.get("", response_model=list[TagWithCount])
async def list_tags(
    q: Optional[str] = Query(
        default=None,
        max_length=64,
        description="Префикс-фильтр для autocomplete. Если задан — limit 10, без counts.",
    ),
    payload=Depends(security.access_token_required),
    service: TagService = Depends(get_tag_service),
):
    user_id = UUID(payload.sub)
    if q:
        return await service.search(user_id, q, limit=10)
    return await service.list_for_user(user_id)


@router.patch("/{tag_id}", response_model=TagShort)
async def rename_tag(
    tag_id: UUID,
    data: TagRename,
    payload=Depends(security.access_token_required),
    service: TagService = Depends(get_tag_service),
):
    user_id = UUID(payload.sub)
    return await service.rename(tag_id, user_id, data)


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: UUID,
    payload=Depends(security.access_token_required),
    service: TagService = Depends(get_tag_service),
):
    user_id = UUID(payload.sub)
    await service.delete(tag_id, user_id)
