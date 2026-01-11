from fastapi import APIRouter, Depends

from core.auth import security

router = APIRouter(
    prefix="/articles",
    tags=["articles"],
    dependencies=[Depends(security.access_token_required)],
)


@router.get("/search/")
async def search_articles(q: str):
    return [
        "a simple graph contrastive learning framework for short text classification",
        "graph-based multimodal contrastive learning for chart question answering",
        "what to align in multimodal contrastive learning?",
        "graph linearization methods for reasoning on graphs with large language models",
        "a heterogeneous multimodal graph learning framework for recognizing user emotions in social networks",
    ]
