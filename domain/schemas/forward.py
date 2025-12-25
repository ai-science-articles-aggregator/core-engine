from pydantic import BaseModel

# TODO(delete): Удалить после сдачи чекпоинта, для моделей будет отдельный микросервис

class ForwardRequest(BaseModel):
    text: str
    max_length: int = 512 # max размер выходного summary
    min_length: int = 100 # min размер выходного summary

class ForwardResponse(BaseModel):
    summary: str