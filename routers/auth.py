from fastapi import APIRouter, Response, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from dependecies.user_di import get_user_service
from domain.schemas.token import TokenResponse, LoginRequest
from domain.schemas.user import UserCreate
from services.user_service import UserService

from core.auth import security

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=TokenResponse)
async def register(
    user_create: UserCreate,
    response: Response,
    service: UserService = Depends(get_user_service)
):
    try:
        resp = await service.create_user(user_create=user_create)

        # Удалить, устанавливать куки на frontend
        security.set_access_cookies(resp.access_token, response)
        security.set_refresh_cookies(resp.refresh_token, response)
        
        return resp
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest,
    response: Response,
    service: UserService = Depends(get_user_service)
):
    try:
        resp = await service.authenticate(email=credentials.email, password=credentials.password)

        # Удалить, устанавливать куки на frontend
        security.set_access_cookies(resp.access_token, response)
        security.set_refresh_cookies(resp.refresh_token, response)

        return resp
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
