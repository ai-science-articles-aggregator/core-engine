from domain.models import Notebook


class NotebookFactory:
    @staticmethod
    def create_notebook(name: str, description: str | None = None) -> Notebook:
        return Notebook(
            name=name,
            description=description,
        )
