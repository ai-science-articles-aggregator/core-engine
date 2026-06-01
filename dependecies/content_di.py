from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from repositories import MessageRepository, NoteRepository, SourceRepository
from services import MessageService, NoteService, SourceService


async def get_source_repository(
    session: AsyncSession = Depends(get_session),
) -> SourceRepository:
    return SourceRepository(session)


async def get_source_service(
    repository: SourceRepository = Depends(get_source_repository),
) -> SourceService:
    return SourceService(repository)


async def get_note_repository(
    session: AsyncSession = Depends(get_session),
) -> NoteRepository:
    return NoteRepository(session)


async def get_note_service(
    repository: NoteRepository = Depends(get_note_repository),
) -> NoteService:
    return NoteService(repository)


async def get_message_repository(
    session: AsyncSession = Depends(get_session),
) -> MessageRepository:
    return MessageRepository(session)


async def get_message_service(
    repository: MessageRepository = Depends(get_message_repository),
) -> MessageService:
    return MessageService(repository)
