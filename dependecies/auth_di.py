from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from dependecies.areas_di import get_area_service
from repositories.user_repository import UserRepository
from services import AreaService, AuthService


async def get_user_repository(
    session: AsyncSession = Depends(get_session),
) -> UserRepository:
    return UserRepository(session)


async def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository),
    area_service: AreaService = Depends(get_area_service),
) -> AuthService:
    return AuthService(user_repo, area_service)
