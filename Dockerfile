FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# gRPC-стабы уже закоммичены в generated/ и попадают в образ через COPY . .
# Генерировать через protoc на сборке не нужно: сабмодуль proto_contracts
# в CI не инициализируется, из-за чего шаг и падал.
COPY . .

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:/app/generated

EXPOSE 8000

CMD ["sh", "-c", "uv run alembic upgrade head && uv run uvicorn main:app --host 0.0.0.0 --port 8000"]
