from fastapi import APIRouter, Depends, HTTPException, Response, status

from core.auth import security
from dependecies import get_auth_service
from domain.schemas import LoginRequest, TokenResponse, UserCreate
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
    response: Response, payload=Depends(security.refresh_token_required)
):
    print(f"payload.sub={payload.sub}")
    user_id = payload.sub

    new_access_token = security.create_access_token(uid=str(user_id))
    new_refresh_token = security.create_refresh_token(uid=str(user_id))

    security.set_access_cookies(new_access_token, response)
    security.set_refresh_cookies(new_refresh_token, response)

    return {"status": "tokens rotated"}
