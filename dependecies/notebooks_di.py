import os
import sys

import grpc

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "generated"))

from fastapi import Depends
from retrieval.v1 import retrieval_pb2_grpc
from sqlalchemy.ext.asyncio import AsyncSession
from agent.v1 import agent_pb2_grpc

from core.config import settings
from database import get_session
from dependecies.areas_di import get_area_service
from dependecies.shares_di import get_share_repository
from dependecies.tags_di import get_tag_service
from repositories import NotebookRepository, ShareRepository
from services import AreaService, NotebookService, TagService

# gRPC-каналы создаём ЛЕНИВО, внутри работающего event loop, а не на импорте.
# grpc.aio привязывает канал к текущему loop; uvicorn поднимает свой loop позже,
# поэтому канал, созданный при импорте, даёт "got Future attached to a different
# loop" при первом вызове → 500. Геттеры async → исполняются в loop сервера.
_rag_channel: grpc.aio.Channel | None = None
_summary_channel: grpc.aio.Channel | None = None


def _get_rag_channel() -> grpc.aio.Channel:
    global _rag_channel
    if _rag_channel is None:
        _rag_channel = grpc.aio.insecure_channel(settings.rag_grpc_url)
    return _rag_channel


def _get_summary_channel() -> grpc.aio.Channel:
    global _summary_channel
    if _summary_channel is None:
        _summary_channel = grpc.aio.insecure_channel(settings.summary_grpc_url)
    return _summary_channel


async def close_grpc_channels() -> None:
    """Корректно закрываем gRPC-каналы при остановке приложения (lifespan)."""
    if _rag_channel is not None:
        await _rag_channel.close()
    if _summary_channel is not None:
        await _summary_channel.close()


async def get_notebooks_repository(
    session: AsyncSession = Depends(get_session),
) -> NotebookRepository:
    return NotebookRepository(session)


async def get_notebooks_service(
    repository: NotebookRepository = Depends(get_notebooks_repository),
    area_service: AreaService = Depends(get_area_service),
    tag_service: TagService = Depends(get_tag_service),
    share_repository: ShareRepository = Depends(get_share_repository),
) -> NotebookService:
    return NotebookService(repository, area_service, tag_service, share_repository)


async def get_rag_stub() -> retrieval_pb2_grpc.RetrievalServiceStub:
    return retrieval_pb2_grpc.RetrievalServiceStub(_get_rag_channel())


async def get_summary_stub() -> agent_pb2_grpc.AgentServiceStub:
    return agent_pb2_grpc.AgentServiceStub(_get_summary_channel())
