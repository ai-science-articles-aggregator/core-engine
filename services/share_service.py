from uuid import UUID

from fastapi import HTTPException, status

from domain.models import Notebook, NotebookShare
from domain.schemas.share import ShareCreate, ShareRead, ShareUpdateMe
from repositories import ShareRepository, UserRepository
from services.area_service import AreaService


class ShareService:
    def __init__(
        self,
        repository: ShareRepository,
        user_repository: UserRepository,
        area_service: AreaService,
    ):
        self.repository = repository
        self.user_repository = user_repository
        self.area_service = area_service

    # ---- read ----

    async def list_for_notebook(
        self, notebook: Notebook, current_user_id: UUID
    ) -> list[ShareRead]:
        if notebook.user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only owner can view shares",
            )
        shares = await self.repository.list_for_notebook(notebook.id)
        return [ShareRead.model_validate(s) for s in shares]

    # ---- write ----

    async def create_share(
        self,
        notebook: Notebook,
        current_user_id: UUID,
        payload: ShareCreate,
    ) -> ShareRead:
        if notebook.user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only owner can create shares",
            )

        # resolve recipient
        if payload.user_id:
            recipient = await self.user_repository.get_user(payload.user_id)
        else:
            recipient = await self.user_repository.get_by_email(payload.user_email)  # type: ignore[arg-type]
        if not recipient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Recipient user not found"
            )

        if recipient.id == current_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot share notebook with yourself",
            )

        # уже шарили?
        existing = await self.repository.get(notebook.id, recipient.id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Notebook already shared with this user",
            )

        share = NotebookShare(
            notebook_id=notebook.id,
            user_id=recipient.id,
            role=payload.role,
            area_id=None,
        )
        share = await self.repository.add(share)

        # Если visibility у owner-а ещё private — переключим в shared,
        # чтобы фронт показывал «есть подписчики».
        if notebook.visibility == "private":
            notebook.visibility = "shared"
            await self.repository.db.commit()

        return ShareRead.model_validate(share)

    async def revoke(
        self, notebook: Notebook, current_user_id: UUID, recipient_user_id: UUID
    ) -> None:
        if notebook.user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only owner can revoke shares",
            )
        share = await self.repository.get(notebook.id, recipient_user_id)
        if not share:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Share not found"
            )
        await self.repository.delete(share)

    async def update_my_share(
        self,
        notebook: Notebook,
        current_user_id: UUID,
        payload: ShareUpdateMe,
    ) -> ShareRead:
        share = await self.repository.get_with_user(notebook.id, current_user_id)
        if not share:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="You don't have a share on this notebook",
            )

        # area_id должна принадлежать current_user (или null = отвязать)
        if payload.area_id is not None:
            await self.area_service.ensure_belongs_to_user(
                payload.area_id, current_user_id
            )

        updated = await self.repository.update_area(share, payload.area_id)
        return ShareRead.model_validate(updated)
