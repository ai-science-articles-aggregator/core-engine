# core-engine

Backend приложение на FastAPI с аутентификацией и базой данных PostgreSQL.

## Требования

- Python 3.13
- PDM (Python Dependency Manager)
- Docker и Docker Compose (для запуска через Docker)

## Настройка окружения

### 1. Копирование файла переменных окружения

Скопируйте файл `.env.example` в `.env` и заполните необходимые значения:

```bash
cp .env.example .env
```

### 2. Описание переменных окружения (.env.example)

#### База данных
- `DATABASE_HOST` - Хост базы данных (по умолчанию: `localhost`, для Docker используйте `postgres`)
- `DATABASE_PORT` - Порт базы данных (по умолчанию: `5432`)
- `DATABASE_NAME` - Имя базы данных (по умолчанию: `appdb`)
- `DATABASE_USER` - Пользователь базы данных (по умолчанию: `root`)
- `DATABASE_PASSWORD` - Пароль базы данных (по умолчанию: `root1234`)

#### JWT (JSON Web Token)
- `SECRET_KEY` - Секретный ключ для подписи JWT токенов (обязательно измените на безопасный ключ!)
- `JWT_ALGORITHM` - Алгоритм подписи JWT (по умолчанию: `HS256`)
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Время жизни access токена в минутах (по умолчанию: `30`)
- `REFRESH_TOKEN_EXPIRE_DAYS` - Время жизни refresh токена в днях (по умолчанию: `7`)
- `JWT_COOKIE_SECURE` - Использовать secure cookies для JWT (по умолчанию: `False`)

#### Приложение
- `DEBUG` - Режим отладки (по умолчанию: `False`)
- `PORT` - Порт приложения (по умолчанию: `8000`)

**Важно:** Обязательно измените `SECRET_KEY` на безопасный случайный ключ в продакшн окружении! Для этого можете воспользоваться утилитой:

```bash
cd core/utils & pdm run python generate_key.py
```

## Запуск приложения

### Локальный запуск (без Docker)

1. Установите зависимости через PDM:

```bash
pdm install
```

2. Убедитесь, что PostgreSQL запущен и доступен по адресу из `.env`

3. Запустите приложение:

```bash
pdm run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Или через Python напрямую:

```bash
pdm run python main.py
```

Приложение будет доступно по адресу: `http://localhost:8000`

### Запуск через Docker Compose

1. Убедитесь, что в файле `.env` указан `DATABASE_HOST=postgres` (имя сервиса в docker-compose)

2. Запустите все сервисы:

```bash
docker-compose up --build
```

Для запуска в фоновом режиме:

```bash
docker-compose up -d --build
```

3. Приложение будет доступно по адресу: `http://localhost:8000`
4. База данных PostgreSQL будет доступна на порту, указанном в `DATABASE_PORT`

### Остановка Docker Compose

Для остановки всех сервисов:

```bash
docker-compose down
```

Для остановки с удалением volumes (данные БД будут удалены):

```bash
docker-compose down -v
```

## API Endpoints

- `GET /health` - Проверка здоровья приложения
- Другие endpoints описаны в роутерах и доступны по `/docs`

## Структура проекта

```
core-engine/
├── alembic/          # Миграции базы данных
├── core/             # Основная логика приложения
│   ├── auth.py       # Аутентификация (настроки JWT)
│   ├── config.py     # Конфигурация приложения
│   └── utils/        # Утилиты
├── domain/           # Доменные модели и схемы
├── dependencies/     # Зависимости (Dependency Injection)
├── repositories/     # Репозитории для работы с БД
├── routers/          # API роутеры
├── services/         # Бизнес-логика
├── main.py           # Точка входа приложения
└── docker-compose.yaml
```
