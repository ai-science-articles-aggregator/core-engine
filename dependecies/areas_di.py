from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from repositories import AreaRepository
from services import AreaService


async def get_area_repository(
    session: AsyncSession = Depends(get_session),
) -> AreaRepository:
    return AreaRepository(session)


async def get_area_service(
    repository: AreaRepository = Depends(get_area_repository),
) -> AreaService:
    return AreaService(repository)
