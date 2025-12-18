from authx import AuthX, AuthXConfig
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # База данных
    db_host: str = Field("localhost", env="DATABASE_HOST")
    db_port: int = Field(5432, env="DATABASE_PORT")
    db_name: str = Field("appdb", env="DATABASE_NAME")
    db_user: str = Field("root", env="DATABASE_USER")
    db_password: str = Field("root1234", env="DATABASE_PASSWORD")
    database_url: str = Field(None, env="DATABASE_URL")

    @property
    def database_url_asyncpg(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    @property
    def database_url_psycopg(self) -> str:
        return f"postgresql+psycopg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    # JWT
    secret_key: str = Field("Your_secret_key", env="SECRET_KEY")
    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    jwt_refresh_token_expire_days: int = Field(7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    jwt_cookie_secure: bool = Field(False, env="JWT_COOKIE_SECURE=False")

    
    # Приложение
    debug: bool = Field(False, env="DEBUG")
    port: int = Field(8000, env="PORT")
    # secret_key: str = Field(..., env="SECRET_KEY")
    
    # Вычисляемое поле
    # @property
    # def database_url(self) -> str:
    #     return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra="allow"

settings = Settings()