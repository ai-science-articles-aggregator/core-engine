from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from repositories import TagRepository
from services import TagService


async def get_tag_repository(
    session: AsyncSession = Depends(get_session),
) -> TagRepository:
    return TagRepository(session)


async def get_tag_service(
    repository: TagRepository = Depends(get_tag_repository),
) -> TagService:
    return TagService(repository)
