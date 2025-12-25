from authx import AuthX, AuthXConfig

from core.config import settings

config = AuthXConfig(
    JWT_ALGORITHM = settings.jwt_algorithm,
    JWT_SECRET_KEY = settings.secret_key,
    JWT_TOKEN_LOCATION = ["headers", "cookies"],

    JWT_ACCESS_COOKIE_NAME="access_token",
    JWT_REFRESH_COOKIE_NAME="refresh_token",

    JWT_ACCESS_TOKEN_EXPIRES=settings.jwt_access_token_expire_minutes * 60,
    JWT_REFRESH_TOKEN_EXPIRES=settings.jwt_refresh_token_expire_days * 86400,

    JWT_COOKIE_SECURE=settings.jwt_cookie_secure,
    JWT_HEADER_TYPE="Bearer",
    JWT_COOKIE_CSRF_PROTECT=False
)

security = AuthX(config=config)