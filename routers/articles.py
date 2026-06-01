from fastapi import APIRouter, Depends

from core.auth import security
from dependecies import get_article_service
from domain.schemas.articles import ArticleRead, ArticlesBatchRequest
from services import ArticleService

router = APIRouter(
    prefix="/articles",
    tags=["articles"],
    dependencies=[Depends(security.access_token_required)],
)


@router.post("/batch", response_model=list[ArticleRead])
async def batch_get_articles(
    data: ArticlesBatchRequest,
    service: ArticleService = Depends(get_article_service),
):
    """Получает метаданные статей из внешней БД (RAG) по списку id.

    Используется фронтом для отображения карточек source'ов:
    фронт берёт `article_id` из `GET /notebooks/:id/sources` и шлёт их сюда
    пакетом, получая обратно `title`/`authors`/`abstract`/`pdf_url`/...

    Поля больших текстов (text, clean_text, sectioned_text) намеренно не возвращаются.
    """
    return await service.batch_get(data.ids)


# ---- legacy mock --------------------------------------------------------
# TODO: убрать когда фронт переключится на POST /search и POST /batch.

@router.get("/search/")
async def search_articles_legacy(q: str):
    return [
        "a simple graph contrastive learning framework for short text classification",
        "graph-based multimodal contrastive learning for chart question answering",
        "what to align in multimodal contrastive learning?",
        "graph linearization methods for reasoning on graphs with large language models",
        "a heterogeneous multimodal graph learning framework for recognizing user emotions in social networks",
    ]
