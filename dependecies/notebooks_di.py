from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from repositories import NotebookRepository
from services import NotebookService


async def get_notebooks_repository(
    session: AsyncSession = Depends(get_session),
) -> NotebookRepository:
    return NotebookRepository(session)


async def get_notebooks_service(
    repository: NotebookRepository = Depends(get_notebooks_repository),
) -> NotebookService:
    return NotebookService(repository)
