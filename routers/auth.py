from fastapi import APIRouter, Depends, HTTPException, Response, status
from uuid import UUID

from core.auth import security
from dependecies import get_auth_service, get_user_repository
from domain.schemas import LoginRequest, TokenResponse, UserCreate, UserResponse
from services import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
async def register(
    user_create: UserCreate,
    response: Response,
    service: AuthService = Depends(get_auth_service),
):
    try:
        resp = await service.create_user(user_create=user_create)

        security.set_access_cookies(resp.access_token, response)
        security.set_refresh_cookies(resp.refresh_token, response)

        return resp
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest,
    response: Response,
    service: AuthService = Depends(get_auth_service),
):
    try:
        resp = await service.authenticate(
            email=credentials.email, password=credentials.password
        )

        security.set_access_cookies(resp.access_token, response)
        security.set_refresh_cookies(resp.refresh_token, response)

        return resp
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.post("/refresh")
async def refresh_token(
    response: Response,
    payload=Depends(security.refresh_token_required)
):
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Refresh token request, payload.sub={payload.sub}")
        user_id = payload.sub

        new_access_token = security.create_access_token(uid=str(user_id))
        new_refresh_token = security.create_refresh_token(uid=str(user_id))

        security.set_access_cookies(new_access_token, response)
        security.set_refresh_cookies(new_refresh_token, response)
        
        logger.info("Tokens rotated successfully")

        return {"status": "tokens rotated", "access_token": new_access_token}
    except Exception as e:
        logger.error(f"Refresh token error: {e}")
        raise HTTPException(status_code=401, detail=f"Token refresh failed: {str(e)}")


@router.post("/logout")
async def logout(response: Response):
    security.unset_access_cookies(response)
    security.unset_refresh_cookies(response)
    return {"message": "Successfully logged out"}


@router.get("/profile", response_model=UserResponse)
async def get_profile(
    response: Response,
    payload=Depends(security.access_token_required),
    user_repo=Depends(get_user_repository),
):
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Profile request, payload.sub={payload.sub}")
        user_id = UUID(payload.sub)
        logger.info(f"Looking for user with ID: {user_id}")
        
        user = await user_repo.get_user(user_id)
        
        if not user:
            logger.warning(f"User not found: {user_id}")
            raise HTTPException(status_code=404, detail="User not found")
        
        logger.info(f"User found: {user.email}")
        return UserResponse.model_validate(user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
