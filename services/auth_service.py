from fastapi import HTTPException
from core.auth import security
from domain.models.user import User
from domain.schemas.token import TokenResponse
from repositories.user_repository import UserRepository
from factories.user_factory import UserFactory
from domain.schemas.user import UserCreate, UserResponse

class AuthService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def create_user(self, user_create: UserCreate) -> TokenResponse:
        existing = await self.repository.get_by_email(user_create.email)

        if existing:
            raise HTTPException(400, "Email уже используется")

        user = UserFactory.create_from_schema(user_create)

        print(f'{user=}')

        await self.repository.add(user)

        access_token = security.create_access_token(uid=str(user.id))
        refresh_token = security.create_refresh_token(uid=str(user.id))

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token
        )

    async def authenticate(self, email: str, password: str) -> TokenResponse:
        user = await self.repository.authenticate(email, password)

        if not user:
            raise HTTPException(401, "Login or Password is not true")

        access_token = security.create_access_token(uid=str(user.id))
        refresh_token = security.create_refresh_token(uid=str(user.id))

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token
        )