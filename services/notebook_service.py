from uuid import UUID

from domain.schemas import NotebookResponse
from factories.notebook_factory import NotebookFactory
from repositories import NotebookRepository


class NotebookService:
    def __init__(self, repository: NotebookRepository):
        self.repository = repository

    async def create_notebook(
        self,
        user_id: UUID,
        name: str = "Новый блокнот",
        description: str | None = None
    ) -> NotebookResponse:
        notebook = NotebookFactory.create_notebook(
            name=name,
            user_id=user_id,
            description=description
        )

        await self.repository.create_notebook(notebook)

        return NotebookResponse.model_validate(notebook)
