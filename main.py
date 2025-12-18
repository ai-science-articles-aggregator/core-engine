import uvicorn

from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel
from contextlib import asynccontextmanager

from core.auth import security
from routers import health, users, auth

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     pass
    # Создание таблиц при старте
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)
    
    # # Подключение Redis
    # redis_client = redis.from_url(str(settings.REDIS_URL))
    # app.state.redis = redis_client
    
    # yield
    
    # # Закрытие соединений при выключении
    # await redis_client.close()
    # await engine.dispose()

app = FastAPI(
    title="Backend",
    version="0.1.0",
    description="",
    # lifespan=lifespan
)

security.handle_errors(app)

app.include_router(health.router)
app.include_router(users.router)
app.include_router(auth.router)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )