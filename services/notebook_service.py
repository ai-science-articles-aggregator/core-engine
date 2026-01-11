from domain.schemas import NotebookResponse
from factories.notebook_factory import NotebookFactory
from repositories import NotebookRepository


class NotebookService:
    def __init__(self, repository: NotebookRepository):
        self.repository = repository

    async def create_notebook(self) -> NotebookResponse:
        notebook = NotebookFactory.create_notebook(name="Новый блокнот")

        await self.repository.create_notebook(notebook)

        return NotebookResponse(
            id=str(notebook.id),
            name=notebook.name,
            description=notebook.description,
            created_at=notebook.created_at,
            updated_at=notebook.updated_at,
        )
