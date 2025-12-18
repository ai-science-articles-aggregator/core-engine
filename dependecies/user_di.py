from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_session
from repositories.user_repository import UserRepository
from services.user_service import UserService

async def get_user_repository(session: AsyncSession = Depends(get_session)) -> UserRepository:
    return UserRepository(session)

async def get_user_service(user_repo: UserRepository = Depends(get_user_repository)) -> UserService:
    return UserService(user_repo)
