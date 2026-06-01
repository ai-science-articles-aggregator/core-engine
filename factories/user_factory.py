from core.utils.hash_password import hash_password
from domain.models.user import User
from domain.schemas.user import UserCreate


class UserFactory:
    @staticmethod
    def create_from_schema(user_create: UserCreate) -> User:
        return User(
            email=user_create.email,
            first_name=user_create.first_name,
            last_name=user_create.last_name,
            department=user_create.department,
            password=hash_password.get_password_hash(user_create.password),
        )
