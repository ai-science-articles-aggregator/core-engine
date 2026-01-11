from typing import Optional

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

    async def get_notebook(self, notebook_id: int) -> Optional[Notebook]:
        return await self.db.get(Notebook, notebook_id)

    # async def update_notebook(
    #     self, notebook_id: int, notebook: Notebook
    # ) -> Optional[Notebook]:
    #     notebook = await self.db.get(Notebook, notebook_id)
    #     if notebook:
    #         notebook.title = notebook.title
    #         notebook.description = notebook.description
    #         await self.db.commit()
    #         await self.db.refresh(notebook)
    #     return notebook

    async def delete_notebook(self, notebook_id: int) -> bool:
        notebook = await self.db.get(Notebook, notebook_id)
        if notebook:
            await self.db.delete(notebook)
            await self.db.commit()
            return True
        return False
