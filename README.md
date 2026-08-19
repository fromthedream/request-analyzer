# Request Analyzer

Сервис для автоматического анализа обращений пользователей с использованием AI.

Пользователь отправляет имя и текст обращения. Система анализирует обращение, определяет категорию, приоритет и тональность, формирует краткое резюме и рекомендуемое действие. Результат сохраняется в PostgreSQL.

## Возможности

* Приём обращений пользователей
* AI-анализ текста
* Определение категории обращения
* Определение приоритета
* Определение тональности
* Формирование краткого резюме
* Формирование рекомендуемого действия
* Сохранение обращений в PostgreSQL
* Просмотр истории обращений
* REST API на FastAPI
* Запуск сервисов через Docker Compose

## Архитектура

```text
Пользователь
     |
     v
HTML / JavaScript
     |
     v
    n8n
     |
     +--------------------+
     |                    |
     v                    v
FastAPI /analyze    FastAPI /requests
     |                    |
     v                    v
  AI-анализ          PostgreSQL
                          |
                          v
                  История обращений
```

## Технологии

* Python 3.12
* FastAPI
* SQLAlchemy
* PostgreSQL 16
* Docker
* Docker Compose
* n8n
* HTML / CSS / JavaScript

## API

### GET `/`

Основная страница анализатора обращений.

### POST `/analyze`

Анализирует обращение.

### POST `/requests`

Сохраняет обращение и результат анализа в PostgreSQL.

### GET `/requests`

Возвращает список сохранённых обращений.

### GET `/requests-page`

Веб-страница с историей обращений.

## Запуск

Для запуска проекта требуется Docker Desktop.

Клонировать репозиторий:

```bash
git clone https://github.com/fromthedream/request-analyzer.git
cd request-analyzer
```

Запустить контейнеры:

```bash
docker compose up -d --build
```

После запуска:

* Анализатор: `http://localhost:8000`
* История обращений: `http://localhost:8000/requests-page`
* FastAPI Swagger: `http://localhost:8000/docs`
* n8n: `http://localhost:5678`

## Структура проекта

```text
request-analyzer/
├── python/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## Пример результата

### Вход

```text
Имя: Антон

Обращение:
Не могу войти в личный кабинет, пароль не помогает
```

### Результат

```json
{
  "category": "авторизация",
  "priority": "high",
  "sentiment": "negative",
  "summary": "Клиент не может войти в личный кабинет, пароль не работает",
  "action": "Проверить учетную запись клиента и сбросить пароль."
}
```

## Что демонстрирует проект

Проект демонстрирует навыки разработки backend-сервисов, работы с REST API, базами данных, Docker-контейнерами и интеграции внешних сервисов через HTTP API.
