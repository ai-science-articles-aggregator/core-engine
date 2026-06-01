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

    # ---- External articles DB (read-only) --------------------------------
    # Метаданные статей живут в отдельной Postgres (питается из RAG-индексера).
    # Если переменные не заданы — fallback на основной DSN (для local-dev,
    # когда обе БД могут быть в одном контейнере).
    articles_db_host: Annotated[
        str | None, Field(alias="ARTICLES_DATABASE_HOST")
    ] = None
    articles_db_port: Annotated[
        int | None, Field(alias="ARTICLES_DATABASE_PORT")
    ] = None
    articles_db_name: Annotated[
        str | None, Field(alias="ARTICLES_DATABASE_NAME")
    ] = None
    articles_db_user: Annotated[
        str | None, Field(alias="ARTICLES_DATABASE_USER")
    ] = None
    articles_db_password: Annotated[
        str | None, Field(alias="ARTICLES_DATABASE_PASSWORD")
    ] = None

    @property
    def articles_database_url_asyncpg(self) -> str:
        host = self.articles_db_host or self.db_host
        port = self.articles_db_port or self.db_port
        name = self.articles_db_name or self.db_name
        user = self.articles_db_user or self.db_user
        password = self.articles_db_password or self.db_password
        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}"

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

    # CORS — либо явный CSV список origin'ов, либо regex для dev-режима.
    # Если cors_origins не пуст, regex игнорируется.
    cors_origins: Annotated[str, Field(alias="CORS_ORIGINS")] = ""
    cors_origin_regex: Annotated[str, Field(alias="CORS_ORIGIN_REGEX")] = (
        r"https?://(localhost|127\.0\.0\.1)(:\d+)?"
    )


settings = Settings()
