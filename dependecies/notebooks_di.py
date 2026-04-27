import os
import sys

import grpc

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "generated"))

from fastapi import Depends
from rag.v1 import rag_pb2_grpc
from sqlalchemy.ext.asyncio import AsyncSession
from summary.v1 import summary_pb2_grpc

from database import get_session
from repositories import NotebookRepository
from services import NotebookService

_rag_channel = grpc.aio.insecure_channel(os.getenv("RAG_GRPC_URL", "localhost:50051"))
_summary_channel = grpc.aio.insecure_channel(
    os.getenv("SUMMARY_GRPC_URL", "localhost:50052")
)


async def get_notebooks_repository(
    session: AsyncSession = Depends(get_session),
) -> NotebookRepository:
    return NotebookRepository(session)


async def get_notebooks_service(
    repository: NotebookRepository = Depends(get_notebooks_repository),
) -> NotebookService:
    return NotebookService(repository)


def get_rag_stub() -> rag_pb2_grpc.RAGServiceStub:
    return rag_pb2_grpc.RAGServiceStub(_rag_channel)


def get_summary_stub() -> summary_pb2_grpc.SummaryServiceStub:
    return summary_pb2_grpc.SummaryServiceStub(_summary_channel)
