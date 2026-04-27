from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # База данных
    db_host: Annotated[str, Field(alias="DATABASE_HOST")] = "localhost"
    db_port: Annotated[int, Field(alias="DATABASE_PORT")] = 5433
    db_name: Annotated[str, Field(alias="DATABASE_NAME")] = "appdb"
    db_user: Annotated[str, Field(alias="DATABASE_USER")] = "root"
    db_password: Annotated[str, Field(alias="DATABASE_PASSWORD")] = "root1234"

    @property
    def database_url_asyncpg(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def database_url_psycopg(self) -> str:
        return f"postgresql+psycopg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    # JWT
    secret_key: Annotated[str, Field(alias="SECRET_KEY")] = "Your_secret_key"
    jwt_algorithm: Annotated[str, Field(alias="JWT_ALGORITHM")] = "HS256"
    jwt_access_token_expire_minutes: Annotated[
        int, Field(alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    ] = 30
    jwt_refresh_token_expire_days: Annotated[
        int, Field(alias="REFRESH_TOKEN_EXPIRE_DAYS")
    ] = 7
    jwt_cookie_secure: Annotated[bool, Field(alias="JWT_COOKIE_SECURE")] = False

    # Приложение
    debug: Annotated[bool, Field(alias="DEBUG")] = False
    port: Annotated[int, Field(alias="PORT")] = 8000


settings = Settings()
