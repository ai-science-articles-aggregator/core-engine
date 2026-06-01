from domain.schemas.articles import ArticleRead
from repositories import ArticleRepository


class ArticleService:
    def __init__(self, repository: ArticleRepository):
        self.repository = repository

    async def batch_get(self, ids: list[str]) -> list[ArticleRead]:
        """Возвращает метаданные статей по списку id из внешней БД.

        Порядок сохраняется как в запросе; статьи, которых нет в БД,
        просто отсутствуют в ответе (фронт сам решит как показывать).
        """
        # дедуп с сохранением порядка
        seen: set[str] = set()
        unique_ids: list[str] = []
        for i in ids:
            if i in seen:
                continue
            seen.add(i)
            unique_ids.append(i)

        articles = await self.repository.get_by_ids(unique_ids)
        by_id = {a.id: a for a in articles}
        return [
            ArticleRead.model_validate(by_id[i])
            for i in unique_ids
            if i in by_id
        ]
