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

COPY proto_contracts/ ./proto_contracts/
RUN mkdir -p generated && uv run python -m grpc_tools.protoc \
    -I ./proto_contracts \
    --python_out=./generated \
    --grpc_python_out=./generated \
    ./proto_contracts/rag/v1/rag.proto \
    ./proto_contracts/summary/v1/summary.proto

COPY . .

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:/app/generated

EXPOSE 8000

CMD ["sh", "-c", "uv run alembic upgrade head && uv run uvicorn main:app --host 0.0.0.0 --port 8000"]
