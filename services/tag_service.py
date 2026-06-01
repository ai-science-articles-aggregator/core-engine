from uuid import UUID

from fastapi import HTTPException, status

from core.utils.slug import slugify
from domain.models import Tag
from domain.schemas.tag import TagRename, TagShort, TagWithCount
from repositories import TagRepository


class TagService:
    def __init__(self, repository: TagRepository):
        self.repository = repository

    # ---- read ----

    async def list_for_user(self, user_id: UUID) -> list[TagWithCount]:
        rows = await self.repository.list_with_counts(user_id)
        return [
            TagWithCount(
                id=tag.id,
                slug=tag.slug,
                name=tag.name,
                notebook_count=count,
            )
            for tag, count in rows
        ]

    async def search(
        self, user_id: UUID, query: str, limit: int = 10
    ) -> list[TagWithCount]:
        tags = await self.repository.search(user_id, query, limit=limit)
        # autocomplete не считает notebook_count (лишний JOIN на каждый prefix-запрос)
        return [
            TagWithCount(id=t.id, slug=t.slug, name=t.name, notebook_count=0)
            for t in tags
        ]

    # ---- write ----

    async def upsert_tags(
        self, user_id: UUID, names: list[str]
    ) -> list[Tag]:
        """Принимает список имён, возвращает list[Tag] (существующие + новые).

        - Дедупает входной список по slug.
        - Пустые после slugify имена пропускает.
        - Новые теги создаются без commit (общая транзакция).
        """
        if not names:
            return []

        # 1. соберём уникальные (slug, name) сохраняя первый встретившийся name
        seen: dict[str, str] = {}
        for raw in names:
            slug = slugify(raw)
            if not slug or slug in seen:
                continue
            seen[slug] = raw.strip()

        if not seen:
            return []

        slugs = list(seen.keys())

        # 2. найдём существующие
        existing = await self.repository.get_by_slugs(user_id, slugs)
        by_slug = {t.slug: t for t in existing}

        # 3. дозальём новые
        for slug, name in seen.items():
            if slug in by_slug:
                continue
            tag = Tag(user_id=user_id, slug=slug, name=name)
            await self.repository.add(tag, commit=False)
            by_slug[slug] = tag

        # вернём в исходном порядке появления уникальных slugs
        return [by_slug[s] for s in slugs]

    async def rename(
        self, tag_id: UUID, user_id: UUID, payload: TagRename
    ) -> TagShort:
        tag = await self.repository.get_for_user(tag_id, user_id)
        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found"
            )
        new_name = payload.name.strip()
        new_slug = slugify(new_name)
        if not new_slug:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tag name must contain at least one alphanumeric character",
            )
        if new_slug != tag.slug:
            clash = await self.repository.get_by_slug(user_id, new_slug)
            if clash and clash.id != tag.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Tag with slug '{new_slug}' already exists",
                )
        updated = await self.repository.update_name_slug(
            tag, name=new_name, slug=new_slug
        )
        return TagShort.model_validate(updated)

    async def delete(self, tag_id: UUID, user_id: UUID) -> None:
        tag = await self.repository.get_for_user(tag_id, user_id)
        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found"
            )
        await self.repository.delete(tag)
