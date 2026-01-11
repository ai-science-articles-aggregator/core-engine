import logging
from contextlib import asynccontextmanager

import uvicorn
from alembic.config import Config
from fastapi import FastAPI

from alembic import command
from core.auth import security
from core.config import settings
from routers import auth, health, notebooks

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


async def lifespan(app: FastAPI):
    run_migrations()


app = FastAPI(title="Backend", version="0.1.0", description="")

security.handle_errors(app)

app.include_router(health, prefix="/api/v1")
app.include_router(auth, prefix="/api/v1")
app.include_router(notebooks, prefix="/api/v1")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
