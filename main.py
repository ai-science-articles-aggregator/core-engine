import logging
from contextlib import asynccontextmanager

import uvicorn
from alembic.config import Config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from alembic import command
from core.auth import security
from core.config import settings
from routers import areas, articles, auth, content, health, notebooks, shares, tags

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("alembic.runtime")


def run_migrations():
    """Миграции"""
    try:
        logger.info("Running DB migrations...")

        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", settings.database_url_psycopg)
        command.upgrade(alembic_cfg, "head")

        logger.info("Migrations applied successfully.")
    except Exception as e:
        logger.error(f"Error running migrations: {e}")
        raise e


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    run_migrations()
    yield
    # shutdown — nothing for now


app = FastAPI(
    title="Backend",
    version="0.1.0",
    description="",
    lifespan=lifespan,
)

# TODO: DELETE
# TODO: DELETE
# Фронт обычно крутится на http://localhost:5173 (Vite/SvelteKit) или :3000 (Next).
# С credentials=True нельзя allow_origins=["*"] — используем regex для гибкости.
# Для прод-деплоя задавай явный список через CORS_ORIGINS в settings (см. core/config.py).
_explicit_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_explicit_origins or [],
    allow_origin_regex=settings.cors_origin_regex if not _explicit_origins else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

security.handle_errors(app)

app.include_router(health, prefix="/api/v1")
app.include_router(auth, prefix="/api/v1")
app.include_router(areas, prefix="/api/v1")
app.include_router(tags, prefix="/api/v1")
app.include_router(notebooks, prefix="/api/v1")
app.include_router(shares, prefix="/api/v1")
app.include_router(content, prefix="/api/v1")
app.include_router(articles, prefix="/api/v1")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
