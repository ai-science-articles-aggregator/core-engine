from typing import Literal, Optional
from uuid import UUID

from domain.models import Notebook, NotebookShare
from domain.schemas import NotebookCreate, NotebookListItem
from domain.schemas.area import AreaShort
from domain.schemas.tag import TagShort
from domain.schemas.user import UserShort
from factories.notebook_factory import NotebookFactory
from repositories import NotebookRepository, ShareRepository
from services.area_service import AreaService
from services.tag_service import TagService


class NotebookService:
    def __init__(
        self,
        repository: NotebookRepository,
        area_service: AreaService,
        tag_service: TagService,
        share_repository: ShareRepository,
    ):
        self.repository = repository
        self.area_service = area_service
        self.tag_service = tag_service
        self.share_repository = share_repository

    # ---- сборка ответа ----

    async def _to_list_item(
        self,
        notebook: Notebook,
        *,
        current_user_id: UUID,
        viewer_share: Optional[NotebookShare] = None,
    ) -> NotebookListItem:
        sources_count, notes_count = await self.repository.counts_for(notebook.id)
        is_owner = notebook.user_id == current_user_id

        # resolve area для конкретного зрителя
        if is_owner:
            area_obj = notebook.area
        else:
            area_obj = viewer_share.area if viewer_share else None
        area_visible = area_obj is not None and area_obj.archived_at is None

        shared_by = None
        if not is_owner:
            shared_by = UserShort.model_validate(notebook.user)

        return NotebookListItem(
            id=notebook.id,
            name=notebook.name,
            description=notebook.description,
            area=AreaShort.model_validate(area_obj) if area_visible else None,
            tags=[TagShort.model_validate(t) for t in notebook.tags],
            visibility=notebook.visibility,  # type: ignore[arg-type]
            is_owner=is_owner,
            shared_by=shared_by,
            sources_count=sources_count,
            notes_count=notes_count,
            created_at=notebook.created_at,
            updated_at=notebook.updated_at,
        )

    # ---- viewer-aware loads ----

    async def list_notebooks(
        self,
        user_id: UUID,
        *,
        owned_only: bool = False,
        shared_only: bool = False,
        visibility: str | None = None,
        area_id: UUID | None = None,
        q: str | None = None,
        tag_slugs: list[str] | None = None,
        tags_op: str = "and",
    ) -> list[NotebookListItem]:
        notebooks = await self.repository.list_for_viewer(
            user_id,
            owned_only=owned_only,
            shared_only=shared_only,
            visibility=visibility,
            area_id=area_id,
            q=q,
            tag_slugs=tag_slugs,
            tags_op=tags_op,  # type: ignore[arg-type]
        )
        # batch-фетч share-записей зрителя для всех найденных тетрадей
        ids = [n.id for n in notebooks if n.user_id != user_id]
        shares = await self.share_repository.list_shares_for_user_and_notebooks(
            user_id, ids
        )
        shares_by_nb = {s.notebook_id: s for s in shares}

        return [
            await self._to_list_item(
                nb,
                current_user_id=user_id,
                viewer_share=shares_by_nb.get(nb.id),
            )
            for nb in notebooks
        ]

    async def get_notebook(
        self, notebook_id: UUID, user_id: UUID
    ) -> NotebookListItem | None:
        notebook = await self.repository.get_notebook(notebook_id)
        if not notebook:
            return None
        viewer_share: NotebookShare | None = None
        if notebook.user_id != user_id:
            viewer_share = await self.share_repository.get_with_user(
                notebook_id, user_id
            )
            if not viewer_share:
                return None
        return await self._to_list_item(
            notebook, current_user_id=user_id, viewer_share=viewer_share
        )

    # ---- авторизация на запись ----

    async def get_role(
        self, notebook: Notebook, current_user_id: UUID
    ) -> Literal["owner", "viewer", "commenter", "editor", None]:
        """Возвращает роль зрителя относительно тетради."""
        if notebook.user_id == current_user_id:
            return "owner"
        share = await self.share_repository.get(notebook.id, current_user_id)
        if not share:
            return None
        return share.role  # type: ignore[return-value]

    # ---- write ----

    async def create_notebook(
        self, user_id: UUID, payload: NotebookCreate
    ) -> NotebookListItem:
        if payload.area_id is not None:
            await self.area_service.ensure_belongs_to_user(payload.area_id, user_id)

        tags = await self.tag_service.upsert_tags(user_id, payload.tags)

        notebook = NotebookFactory.create_notebook(
            name=payload.name,
            user_id=user_id,
            description=payload.description,
            area_id=payload.area_id,
            visibility=payload.visibility,
        )
        notebook.tags = tags
        notebook = await self.repository.create_notebook(notebook)
        return await self._to_list_item(notebook, current_user_id=user_id)

    async def update_notebook(
        self,
        notebook_id: UUID,
        user_id: UUID,
        payload: NotebookCreate,
    ) -> NotebookListItem | None:
        clear_area = "area_id" in payload.model_fields_set and payload.area_id is None
        if payload.area_id is not None:
            await self.area_service.ensure_belongs_to_user(payload.area_id, user_id)

        new_tags = None
        if "tags" in payload.model_fields_set:
            new_tags = await self.tag_service.upsert_tags(user_id, payload.tags)

        notebook = await self.repository.update_notebook(
            notebook_id=notebook_id,
            name=payload.name,
            description=payload.description,
            area_id=payload.area_id,
            visibility=payload.visibility,
            clear_area=clear_area,
            tags=new_tags,
        )
        if not notebook:
            return None
        return await self._to_list_item(notebook, current_user_id=user_id)

