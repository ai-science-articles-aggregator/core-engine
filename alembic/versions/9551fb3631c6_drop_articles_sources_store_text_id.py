"""drop articles, sources store text id

Revision ID: 9551fb3631c6
Revises: e0f0d3f4d3e9
Create Date: 2026-05-27 17:25:07.264034

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9551fb3631c6'
down_revision: Union[str, Sequence[str], None] = 'e0f0d3f4d3e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    Цель: убрать локальный кэш статей. Статьи живут в RAG (внешняя БД),
    у нас в `notebook_sources` хранится только text-id и `selected`.
    """
    # 1. дропнуть FK notebook_sources.article_id → articles.id
    op.drop_constraint(
        op.f('notebook_sources_article_id_fkey'),
        'notebook_sources',
        type_='foreignkey',
    )
    # 2. сменить тип колонки UUID → varchar(255) с USING-кастом
    op.alter_column(
        'notebook_sources',
        'article_id',
        existing_type=sa.UUID(),
        type_=sa.String(length=255),
        existing_nullable=False,
        postgresql_using='article_id::text',
    )
    # 3. дропнуть таблицу articles вместе с её индексами/FK
    op.drop_index(op.f('ix_articles_arxiv_id'), table_name='articles')
    op.drop_index(op.f('ix_articles_id'), table_name='articles')
    op.drop_index(op.f('ix_articles_notebook_id'), table_name='articles')
    op.drop_table('articles')


def downgrade() -> None:
    """Downgrade schema."""
    op.create_table(
        'articles',
        sa.Column('id', sa.UUID(), autoincrement=False, nullable=False),
        sa.Column('notebook_id', sa.UUID(), autoincrement=False, nullable=False),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
        sa.Column('arxiv_id', sa.VARCHAR(length=255), autoincrement=False, nullable=False),
        sa.Column('title', sa.VARCHAR(length=500), autoincrement=False, nullable=False),
        sa.Column('authors', sa.TEXT(), autoincrement=False, nullable=True),
        sa.Column('score', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
        sa.Column('query', sa.TEXT(), autoincrement=False, nullable=True),
        sa.ForeignKeyConstraint(['notebook_id'], ['notebooks.id'], name=op.f('fk_articles_notebook_id'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('articles_pkey')),
    )
    op.create_index(op.f('ix_articles_notebook_id'), 'articles', ['notebook_id'], unique=False)
    op.create_index(op.f('ix_articles_id'), 'articles', ['id'], unique=False)
    op.create_index(op.f('ix_articles_arxiv_id'), 'articles', ['arxiv_id'], unique=False)
    op.alter_column(
        'notebook_sources',
        'article_id',
        existing_type=sa.String(length=255),
        type_=sa.UUID(),
        existing_nullable=False,
        postgresql_using='article_id::uuid',
    )
    op.create_foreign_key(
        op.f('notebook_sources_article_id_fkey'),
        'notebook_sources', 'articles',
        ['article_id'], ['id'],
        ondelete='CASCADE',
    )
