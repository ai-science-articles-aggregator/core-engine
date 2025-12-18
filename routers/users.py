from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_session
from domain.schemas.user import UserCreate, UserResponse
from services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])

async def get_user_service(
    session: AsyncSession = Depends(get_session)
):
    return UserService(db=session)

@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(
    user: UserCreate,
    service: UserService = Depends(get_user_service)
):
    """
    Роут делает ТОЛЬКО HTTP логику
    Вся бизнес-логика в сервисе
    """
    return await service.create_user(user)

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service)
):
    """Получить пользователя"""
    return await service.get_user(user_id)