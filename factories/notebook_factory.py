from uuid import UUID

from domain.models import Notebook


class NotebookFactory:
    @staticmethod
    def create_notebook(
        name: str,
        user_id: UUID,
        description: str | None = None
    ) -> Notebook:
        return Notebook(
            name=name,
            description=description,
            user_id=user_id,
        )
