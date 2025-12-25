FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir pdm

COPY pyproject.toml pdm.lock ./

RUN pdm config python.use_venv false \
    && pdm install --prod --frozen-lockfile

COPY . .

EXPOSE 8000

CMD ["pdm", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]