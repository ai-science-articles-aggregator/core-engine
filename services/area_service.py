from uuid import UUID

from fastapi import HTTPException, status

from core.constants.areas import DEFAULT_AREAS
from core.utils.slug import slugify
from domain.models import Area
from domain.schemas.area import AreaCreate, AreaRead, AreaUpdate
from repositories import AreaRepository


class AreaService:
    def __init__(self, repository: AreaRepository):
        self.repository = repository

    # ---- seeding ----

    async def seed_default_areas(self, user_id: UUID) -> None:
        """Сидит 10 дефолтных областей. Вызывается при регистрации."""
        areas = [
            Area(
                user_id=user_id,
                slug=slugify(name),
                name=name,
                palette_key=palette,
            )
            for name, palette in DEFAULT_AREAS
        ]
        await self.repository.bulk_add(areas)

    # ---- CRUD ----

    async def list_for_user(self, user_id: UUID) -> list[AreaRead]:
        areas = await self.repository.list_active_for_user(user_id)
        return [AreaRead.model_validate(a) for a in areas]

    async def create(self, user_id: UUID, payload: AreaCreate) -> AreaRead:
        slug = slugify(payload.name)
        if not slug:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Area name must contain at least one alphanumeric character",
            )
        if await self.repository.get_by_slug(user_id, slug):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Area with slug '{slug}' already exists",
            )
        area = Area(
            user_id=user_id,
            slug=slug,
            name=payload.name.strip(),
            palette_key=payload.palette_key,
        )
        await self.repository.add(area)
        return AreaRead.model_validate(area)

    async def update(
        self, area_id: UUID, user_id: UUID, payload: AreaUpdate
    ) -> AreaRead:
        area = await self.repository.get_active_for_user(area_id, user_id)
        if not area:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Area not found"
            )

        new_slug: str | None = None
        new_name: str | None = None
        if payload.name is not None:
            new_name = payload.name.strip()
            new_slug = slugify(new_name)
            if not new_slug:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Area name must contain at least one alphanumeric character",
                )
            if new_slug != area.slug:
                clash = await self.repository.get_by_slug(user_id, new_slug)
                if clash and clash.id != area.id:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Area with slug '{new_slug}' already exists",
                    )

        updated = await self.repository.update(
            area,
            name=new_name,
            slug=new_slug,
            palette_key=payload.palette_key,
        )
        return AreaRead.model_validate(updated)

    async def soft_delete(self, area_id: UUID, user_id: UUID) -> None:
        area = await self.repository.get_active_for_user(area_id, user_id)
        if not area:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Area not found"
            )
        await self.repository.soft_delete(area)

    # ---- внутреннее (для NotebookService) ----

    async def ensure_belongs_to_user(self, area_id: UUID, user_id: UUID) -> Area:
        """Возвращает Area если она принадлежит юзеру и не архивирована, иначе 400."""
        area = await self.repository.get_active_for_user(area_id, user_id)
        if not area:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="area_id does not belong to current user",
            )
        return area
