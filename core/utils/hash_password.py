from passlib.context import CryptContext

class HashPassword:
    def __init__(self):
        pwd_context = CryptContext(
            schemes=["argon2"],
            deprecated="auto",
        )

        self.context = pwd_context

    def get_password_hash(self, password: str) -> str:
        return self.context.hash(password)   

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.context.verify(plain_password, hashed_password)

hash_password = HashPassword()