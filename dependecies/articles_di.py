from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from articles_db import get_articles_session
from repositories import ArticleRepository
from services import ArticleService


async def get_article_repository(
    session: AsyncSession = Depends(get_articles_session),
) -> ArticleRepository:
    return ArticleRepository(session)


async def get_article_service(
    repository: ArticleRepository = Depends(get_article_repository),
) -> ArticleService:
    return ArticleService(repository)
