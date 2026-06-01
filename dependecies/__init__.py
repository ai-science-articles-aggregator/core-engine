from .areas_di import get_area_repository, get_area_service
from .articles_di import get_article_repository, get_article_service
from .auth_di import get_auth_service, get_user_repository
from .content_di import (
    get_message_repository,
    get_message_service,
    get_note_repository,
    get_note_service,
    get_source_repository,
    get_source_service,
)
from .notebooks_di import get_notebooks_service, get_rag_stub, get_summary_stub
from .shares_di import get_share_repository, get_share_service
from .tags_di import get_tag_repository, get_tag_service

__all__ = [
    "get_area_repository",
    "get_area_service",
    "get_article_repository",
    "get_article_service",
    "get_auth_service",
    "get_user_repository",
    "get_message_repository",
    "get_message_service",
    "get_note_repository",
    "get_note_service",
    "get_notebooks_service",
    "get_rag_stub",
    "get_summary_stub",
    "get_share_repository",
    "get_share_service",
    "get_source_repository",
    "get_source_service",
    "get_tag_repository",
    "get_tag_service",
]
