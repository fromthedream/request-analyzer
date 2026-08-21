# Request Analyzer

Request Analyzer — система автоматического анализа пользовательских обращений с использованием n8n, локальной LLM и PostgreSQL. Проект запускается через Docker Compose и объединяет Python API, AuthApi, n8n и один контейнер PostgreSQL.

## Архитектура

```text
Browser
  |
  | POST /webhook/request-analyzer
  v
n8n Webhook
  |
  | POST /analyze + Authorization
  v
Python API (FastAPI)
  |
  +--> n8n -> Ollama / qwen3:8b -> анализ обращения
  |
  +--> POST /requests -> PostgreSQL request_analyzer
  |
  +--> GET /requests <- Authorization JWT

Browser -- login --> AuthApi -- EF Core --> PostgreSQL authapi
```

- **n8n** принимает обращение через Webhook, передаёт его на Python API, запускает AI-анализ через Ollama и сохраняет результат.
- **Python API** валидирует входные данные, обслуживает веб-интерфейс, сохраняет обращения и отдаёт историю.
- **AuthApi** отвечает за регистрацию, login, access/refresh tokens, JWT-проверку и профиль пользователя.
- **PostgreSQL** работает одним контейнером с двумя базами: `request_analyzer` и `authapi`.
- **Docker Compose** подключает все контейнеры к общей внутренней сети. AuthApi и Python ждут `service_healthy` для PostgreSQL.

## Структура репозитория

```text
request-analyzer/
├── authapi/
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── AuthApi.csproj
│   ├── Program.cs
│   ├── Data/
│   ├── Migrations/
│   ├── Models/
│   ├── Services/
│   └── Properties/
├── python/
│   ├── Dockerfile
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   └── requirements.txt
├── n8n/
│   └── request-analyzer.json
├── init-db/
│   └── 01-create-authapi.sql
├── tests/
│   ├── conftest.py
│   ├── test_analyze.py
│   └── test_requests.py
├── screenshots/
├── docker-compose.yml
├── .gitignore
└── README.md
```

## Технологический стек

- C# / ASP.NET Core / .NET 10;
- Entity Framework Core 10;
- PostgreSQL 16;
- JWT с алгоритмом HS256;
- BCrypt для хеширования паролей;
- Python 3.12;
- FastAPI, Uvicorn, Pydantic, SQLAlchemy;
- n8n;
- Ollama и модель `qwen3:8b`;
- Docker и Docker Compose;
- pytest.

## Возможности

- регистрация пользователя и вход через AuthApi;
- выдача и обновление access token;
- отзыв refresh token;
- защищённый профиль пользователя;
- HTML-интерфейс анализа обращений;
- передача JWT из браузера в n8n и далее в Python `/analyze`;
- проверка входного обращения;
- определение категории, приоритета и тональности через локальную LLM;
- формирование резюме и рекомендуемого действия;
- сохранение обращения и результата в PostgreSQL;
- просмотр истории обращений;
- автоматизация workflow через n8n;
- API-тесты на pytest.

## Запуск через Docker Compose

### Prerequisites

Для запуска нужны:

- Docker Desktop с Docker Compose;
- Ollama, запущенная на хост-системе;
- модель Ollama `qwen3:8b`.

Загрузка модели:

```bash
ollama pull qwen3:8b
```

n8n обращается к Ollama через `http://host.docker.internal:11434/api/generate`. Этот адрес уже указан в workflow.

### Переменные окружения

Создайте локальный `.env` в корне репозитория. Реальные значения не должны попадать в Git.

Необходимая переменная:

```env
JWT_SECRET_KEY=<локальный signing key>
```

Compose также поддерживает следующие переменные с безопасными значениями по умолчанию для issuer, audience и algorithm:

```env
JWT_ISSUER=AuthApi
JWT_AUDIENCE=AuthApiClient
JWT_ALGORITHM=HS256
```

`JWT_SECRET_KEY` передаётся Python как `JWT_SECRET_KEY` и AuthApi как `Jwt__Key`. Ключ должен быть одинаковым для обоих сервисов.

### Запуск

```bash
docker compose up --build
```

Или в фоне:

```bash
docker compose up -d --build
```

Остановка без удаления данных:

```bash
docker compose stop
```

PostgreSQL имеет healthcheck:

```text
pg_isready -U analyzer -d request_analyzer
```

Python и AuthApi зависят от `postgres` с condition `service_healthy`, поэтому стартуют после готовности PostgreSQL. При запуске AuthApi вызывает `Database.Migrate()` и автоматически применяет отсутствующие EF Core migrations к базе `authapi`.

### Сервисы и порты

| Сервис | Назначение | Адрес |
|---|---|---|
| Python | FastAPI и веб-интерфейс | `http://localhost:8000` |
| AuthApi | Регистрация, JWT и профиль | `http://localhost:5054` |
| n8n | Workflow automation | `http://localhost:5678` |
| PostgreSQL | Внутренняя база данных | `postgres:5432` внутри Compose-сети |

PostgreSQL не публикуется отдельным host-портом в текущем Compose; сервисы подключаются к нему по имени `postgres`.

## AuthApi

Исходники находятся в `authapi/`. AuthApi использует ASP.NET Core, EF Core, Npgsql, BCrypt и JWT.

### Endpoints

| Метод | Endpoint | Назначение |
|---|---|---|
| `POST` | `/register` | Регистрация пользователя |
| `POST` | `/login` | Проверка credentials и выдача access/refresh tokens |
| `POST` | `/refresh` | Выдача нового access token по refresh token |
| `POST` | `/logout` | Отзыв refresh token |
| `GET` | `/profile` | Профиль текущего JWT-пользователя; требует authorization |

JWT использует значения `Jwt:Key`, `Jwt:Issuer` и `Jwt:Audience`, передаваемые в контейнер через environment variables. Access token содержит identity claims пользователя и проверяется по issuer, audience, сроку действия и signing key.

EF Core migrations находятся в `authapi/Migrations/`. При запуске приложения они применяются к базе `authapi` через `Database.Migrate()`.

## Request Analyzer

Python API находится в `python/` и запускается Uvicorn на порту `8000`.

### Endpoints

| Метод | Endpoint | Назначение |
|---|---|---|
| `GET` | `/` | Главная HTML-страница с login и формой обращения |
| `POST` | `/analyze` | Обрезает и валидирует имя/сообщение, считает длину и слова |
| `POST` | `/requests` | Сохраняет результат анализа в PostgreSQL; используется n8n |
| `GET` | `/requests` | Возвращает историю; требует Bearer JWT |
| `GET` | `/requests-page` | HTML-страница истории с login в браузере |

На главной странице браузер получает access token через `POST http://localhost:5054/login`, хранит его только в памяти JavaScript и передаёт как `Authorization: Bearer ...` в n8n Webhook. n8n прокидывает исходный заголовок в Python `/analyze`. Страница истории аналогично получает токен через AuthApi и использует его при `GET /requests`.

Передача заголовка в `/analyze` настроена для интеграционного потока, но сам endpoint `/analyze` сейчас не защищён JWT dependency. `POST /requests` также не защищён dependency и используется n8n для сохранения результата; JWT-защита применяется к `GET /requests`.

Python подключается к базе `request_analyzer` через внутреннее имя Docker-сервиса `postgres`.

## n8n

Workflow находится в `n8n/request-analyzer.json`.

Основной путь:

```text
Webhook POST /webhook/request-analyzer
  -> HTTP Request POST http://host.docker.internal:8000/analyze
  -> If
  -> Analyze with AI -> Ollama qwen3:8b
  -> Merge
  -> HTTP Request POST http://python:8000/requests
  -> Respond to Webhook
```

Webhook принимает JSON с `name` и `message`. HTTP Request для `/analyze` передаёт входящий `Authorization` без декодирования через выражение:

```text
$json.headers.authorization
```

После анализа workflow объединяет исходные данные с полями `category`, `priority`, `sentiment`, `summary` и `action`, сохраняет их через `POST /requests` и возвращает JSON-ответ браузеру.

## База данных

Один контейнер PostgreSQL содержит две базы:

- `request_analyzer` — данные обращений Python API;
- `authapi` — пользователи и refresh tokens AuthApi.

База `authapi` создаётся init-скриптом `init-db/01-create-authapi.sql`. База `request_analyzer` создаётся через `POSTGRES_DB` в Compose.

Основные таблицы:

`request_analyzer`:

- `requests` — обращение, исходный текст, метрики, категория, приоритет, тональность, резюме и действие.

`authapi`:

- `Users` — имя пользователя и хеш пароля;
- `RefreshTokens` — refresh tokens, срок действия, отзыв и связь с пользователем;
- `__EFMigrationsHistory` — история применённых EF Core migrations.

## Разработка и тестирование

Локальная установка Python-зависимостей описана в `python/requirements.txt`. Для запуска тестов используйте окружение проекта:

```bash
python -m pip install -r python/requirements.txt
python -m pytest -q
```

Тесты находятся в `tests/` и проверяют `/analyze`, сохранение обращений и JWT-защиту `/requests`.

Для проверки Docker-конфигурации без запуска контейнеров:

```bash
docker compose config
```

Для сборки AuthApi через Compose:

```bash
docker compose build authapi
```

Полный запуск и сборка всех сервисов:

```bash
docker compose up --build
```

## Безопасность

- Не добавляйте в Git `.env`, реальные JWT signing keys, access tokens, refresh tokens или пароли.
- Не переносите `appsettings.Development.json` с локальными секретами.
- Не используйте реальные токены в `AuthApi.http` или других тестовых файлах.
- `JWT_SECRET_KEY` должен задаваться через `.env` или внешнюю переменную окружения.
- Для AuthApi ключ передаётся как `Jwt__Key`, для Python — как `JWT_SECRET_KEY`.
- JWT проверяется по алгоритму HS256, issuer, audience, сроку действия и подписи.
- PostgreSQL доступен сервисам внутри Compose-сети по адресу `postgres:5432`.
- Для реального production-развёртывания секреты следует хранить во внешнем secret manager, а не в файлах проекта.

## Docker Compose

Docker Compose является основным способом запуска проекта. Он собирает `python/` и `authapi/`, запускает n8n и PostgreSQL, создаёт внутреннюю сеть, подключает volumes и управляет порядком запуска по healthcheck PostgreSQL.
