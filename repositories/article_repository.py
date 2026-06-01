"""Read-only репозиторий для внешней БД статей."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.external.article import Article


class ArticleRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_ids(self, ids: list[str]) -> list[Article]:
        if not ids:
            return []
        result = await self.db.execute(
            select(Article).where(Article.id.in_(ids))
        )
        return list(result.scalars().all())
