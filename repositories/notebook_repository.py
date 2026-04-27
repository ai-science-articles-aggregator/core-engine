from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.models import Notebook


class NotebookRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_notebook(self, notebook: Notebook) -> Notebook:
        self.db.add(notebook)
        await self.db.commit()
        await self.db.refresh(notebook)
        return notebook

    async def get_notebook(self, notebook_id: UUID) -> Optional[Notebook]:
        return await self.db.get(Notebook, notebook_id)

    async def get_notebooks_by_user(self, user_id: UUID) -> list[Notebook]:
        result = await self.db.execute(
            select(Notebook).where(Notebook.user_id == user_id)
        )
        return result.scalars().all()

    async def update_notebook(
        self, notebook_id: UUID, name: str | None = None, description: str | None = None
    ) -> Optional[Notebook]:
        notebook = await self.get_notebook(notebook_id)
        if notebook:
            if name:
                notebook.name = name
            if description is not None:
                notebook.description = description
            await self.db.commit()
            await self.db.refresh(notebook)
        return notebook

    async def delete_notebook(self, notebook_id: UUID) -> bool:
        notebook = await self.get_notebook(notebook_id)
        if notebook:
            await self.db.delete(notebook)
            await self.db.commit()
            return True
        return False

    async def save_search_results(
        self,
        notebook_id: UUID,
        query: str,
        articles: list[dict],
    ) -> None:
        from domain.models import Article

        for article_data in articles:
            article = Article(
                arxiv_id=article_data["id"],
                title=article_data["title"],
                authors=article_data["authors"],
                score=article_data["score"],
                query=query,
                notebook_id=notebook_id,
            )
            self.db.add(article)

        await self.db.commit()
