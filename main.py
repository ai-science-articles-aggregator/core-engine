import uvicorn
import logging

from fastapi import FastAPI
from contextlib import asynccontextmanager

from core.auth import security
from core.config import settings
from routers import health, auth, forward
from services import SummarizationService
from alembic.config import Config
from alembic import command

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("alembic.runtime")

def run_migrations():
    """Миграции"""
    try:
        logger.info("Running DB migrations...")

        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", settings.database_url_asyncpg + "?async_fallback=True")
        command.upgrade(alembic_cfg, "head")

        logger.info("Migrations applied successfully.")
    except Exception as e:
        logger.error(f"Error running migrations: {e}")
        raise e


@asynccontextmanager
async def lifespan(app: FastAPI):
    # TODO(delete): Удалить после сдачи чекпоинта, для моделей будет отдельный микросервис
    ml_service = SummarizationService("allenai/led-large-16384-arxiv")
    ml_service.load_model()
    app.state.ml_service = ml_service
    yield
    del app.state.ml_service

app = FastAPI(
    title="Backend",
    version="0.1.0",
    description="",
    lifespan=lifespan
)

security.handle_errors(app)

app.include_router(health)
app.include_router(auth)
app.include_router(forward)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )