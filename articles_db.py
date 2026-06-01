"""Подключение к внешней БД статей (read-only).

Эта БД питается RAG-индексером и содержит метаданные статей (id, arxiv_id,
title, authors, abstract, ...). core-engine только читает её, чтобы отдавать
фронту мету по id'ам из notebook_sources.
"""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from core.config import settings


class ArticlesBase(DeclarativeBase):
    """Отдельный DeclarativeBase, чтобы наш alembic не цеплял эти модели."""

    pass


articles_engine = create_async_engine(
    settings.articles_database_url_asyncpg,
    echo=False,
    future=True,
)

articles_session_maker = async_sessionmaker(
    bind=articles_engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_articles_session() -> AsyncSession:
    """Async-сессия для чтения из БД статей."""
    async with articles_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
