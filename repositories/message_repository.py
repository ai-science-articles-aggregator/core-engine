from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.models import NotebookChatMessage, NotebookSource


class MessageRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_for_notebook(
        self, notebook_id: UUID
    ) -> list[NotebookChatMessage]:
        result = await self.db.execute(
            select(NotebookChatMessage)
            .where(NotebookChatMessage.notebook_id == notebook_id)
            .order_by(NotebookChatMessage.created_at.asc())
        )
        return list(result.scalars().all())

    async def add(
        self, message: NotebookChatMessage
    ) -> NotebookChatMessage:
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def selected_arxiv_ids(self, notebook_id: UUID) -> list[str]:
        """arxiv_id всех selected sources тетради — для передачи в summary_stub."""
        from domain.models import Article

        result = await self.db.execute(
            select(Article.arxiv_id)
            .join(NotebookSource, NotebookSource.article_id == Article.id)
            .where(
                NotebookSource.notebook_id == notebook_id,
                NotebookSource.selected.is_(True),
            )
        )
        return [row[0] for row in result.all() if row[0]]
