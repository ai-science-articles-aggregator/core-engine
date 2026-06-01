from uuid import UUID

from fastapi import APIRouter, Depends, status

from core.auth import security
from dependecies import get_area_service
from domain.schemas.area import AreaCreate, AreaRead, AreaUpdate
from services import AreaService

router = APIRouter(
    prefix="/areas",
    tags=["areas"],
    dependencies=[Depends(security.access_token_required)],
)


@router.get("", response_model=list[AreaRead])
async def list_areas(
    payload=Depends(security.access_token_required),
    service: AreaService = Depends(get_area_service),
):
    user_id = UUID(payload.sub)
    return await service.list_for_user(user_id)


@router.post("", response_model=AreaRead, status_code=status.HTTP_201_CREATED)
async def create_area(
    data: AreaCreate,
    payload=Depends(security.access_token_required),
    service: AreaService = Depends(get_area_service),
):
    user_id = UUID(payload.sub)
    return await service.create(user_id, data)


@router.patch("/{area_id}", response_model=AreaRead)
async def update_area(
    area_id: UUID,
    data: AreaUpdate,
    payload=Depends(security.access_token_required),
    service: AreaService = Depends(get_area_service),
):
    user_id = UUID(payload.sub)
    return await service.update(area_id, user_id, data)


@router.delete("/{area_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_area(
    area_id: UUID,
    payload=Depends(security.access_token_required),
    service: AreaService = Depends(get_area_service),
):
    user_id = UUID(payload.sub)
    await service.soft_delete(area_id, user_id)
