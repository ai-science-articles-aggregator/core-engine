from domain.models.user import User
from domain.schemas.user import UserCreate
from core.utils.hash_password import hash_password

class UserFactory:
    @staticmethod
    def create_from_schema(user_create: UserCreate) -> User:
        return User(
            email=user_create.email,
            username=user_create.username,
            password=hash_password.get_password_hash(user_create.password)
        )