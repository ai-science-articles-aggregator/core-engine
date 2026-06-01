from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from dependecies.areas_di import get_area_service
from dependecies.auth_di import get_user_repository
from repositories import ShareRepository, UserRepository
from services import AreaService, ShareService


async def get_share_repository(
    session: AsyncSession = Depends(get_session),
) -> ShareRepository:
    return ShareRepository(session)


async def get_share_service(
    repository: ShareRepository = Depends(get_share_repository),
    user_repository: UserRepository = Depends(get_user_repository),
    area_service: AreaService = Depends(get_area_service),
) -> ShareService:
    return ShareService(repository, user_repository, area_service)
