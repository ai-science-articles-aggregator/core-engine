"""users: drop username/full_name, add first_name/last_name/department

Revision ID: 529bb7e4b78c
Revises: 9551fb3631c6
Create Date: 2026-05-28 23:58:39.512424

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '529bb7e4b78c'
down_revision: Union[str, Sequence[str], None] = '9551fb3631c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    Юзер-контракт под форму регистрации: first_name + last_name + faculty/department.
    username и full_name больше не используются.

    Внимание: если в users уже есть строки — миграция упадёт, потому что
    добавляются NOT NULL колонки без default. Это намеренно: имена обязательны
    для регистрации, пустые значения в БД не нужны. Перед накатом сделай
    TRUNCATE users CASCADE (dev) или backfill (prod).
    """
    op.add_column('users', sa.Column('first_name', sa.String(length=100), nullable=False))
    op.add_column('users', sa.Column('last_name', sa.String(length=100), nullable=False))
    op.add_column('users', sa.Column('department', sa.String(length=255), nullable=True))

    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_column('users', 'username')
    op.drop_column('users', 'full_name')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column(
        'users',
        sa.Column('full_name', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    )
    op.add_column(
        'users',
        sa.Column('username', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    )
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.drop_column('users', 'department')
    op.drop_column('users', 'last_name')
    op.drop_column('users', 'first_name')
