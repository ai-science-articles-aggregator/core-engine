from .areas import router as areas
from .articles import router as articles
from .auth import router as auth
from .content import router as content
from .health import router as health
from .notebooks import router as notebooks
from .shares import router as shares
from .tags import router as tags

__all__ = ["areas", "articles", "auth", "content", "health", "notebooks", "shares", "tags"]
