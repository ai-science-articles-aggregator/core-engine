"""Read-only маппинг таблицы `articles` из внешней RAG БД.

Используем отдельный `ArticlesBase`, чтобы наш alembic эту таблицу не трогал.
Мапим подмножество колонок, нужных фронту в карточке source'а. Большие поля
(text / clean_text / sectioned_text / section_text_new / references_id) НЕ грузим.

ВАЖНО: `articles.id` — это text-идентификатор статьи, совпадающий с
`search_e5_large_new.article_id`, который retrieval возвращает как ArticleResult.id.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, Text
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column

from articles_db import ArticlesBase


class Article(ArticlesBase):
    __tablename__ = "articles"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    arxiv_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    title: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    authors: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    abstract: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    published: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=False), nullable=True
    )
    categories: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    doi: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    journal_ref: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    primary_category: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    num_pages: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pdf_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
