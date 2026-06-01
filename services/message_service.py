import json
from typing import AsyncIterator
from uuid import UUID

import grpc

from domain.models import NotebookChatMessage
from domain.schemas.messages import ChatMessageCreate, ChatMessageRead
from repositories import MessageRepository


class MessageService:
    def __init__(self, repository: MessageRepository):
        self.repository = repository

    async def list_for_notebook(
        self, notebook_id: UUID
    ) -> list[ChatMessageRead]:
        msgs = await self.repository.list_for_notebook(notebook_id)
        return [ChatMessageRead.model_validate(m) for m in msgs]

    async def post_user_message(
        self, notebook_id: UUID, payload: ChatMessageCreate
    ) -> NotebookChatMessage:
        user_msg = NotebookChatMessage(
            notebook_id=notebook_id,
            role="user",
            text=payload.text,
            citations=[],
        )
        return await self.repository.add(user_msg)

    async def stream_assistant_reply(
        self,
        notebook_id: UUID,
        user_text: str,
        summary_stub,
    ) -> AsyncIterator[str]:
        """SSE-friendly async generator.

        Стримит токены через summary-сервис (используются selected sources),
        собирает финальный текст и сохраняет assistant-message в БД.
        Если summary недоступен или нет sources — fallback к простому ответу.
        """
        from summary.v1 import summary_pb2  # local import — generated code

        article_ids = await self.repository.selected_arxiv_ids(notebook_id)

        assembled_tokens: list[str] = []
        had_error = False

        async def emit(data: dict) -> str:
            return f"data: {json.dumps(data)}\n\n"

        if not article_ids:
            # Нет выбранных источников — даём короткий fallback,
            # не дёргаем gRPC.
            fallback = "Select at least one source to ground the answer."
            assembled_tokens.append(fallback)
            yield await emit({"token": fallback})
        else:
            try:
                async for response in summary_stub.Summarize(
                    summary_pb2.SummarizeRequest(
                        article_ids=article_ids, query=user_text
                    )
                ):
                    tok = response.token
                    assembled_tokens.append(tok)
                    yield await emit({"token": tok})
            except grpc.aio.AioRpcError as e:
                had_error = True
                yield await emit({"error": e.details()})

        # сохраним собранный ответ assistant (даже если ошибка — пустой текст)
        assistant_msg = NotebookChatMessage(
            notebook_id=notebook_id,
            role="assistant" if not had_error else "system",
            text="".join(assembled_tokens),
            citations=[],
        )
        await self.repository.add(assistant_msg)

        yield "data: [DONE]\n\n"
