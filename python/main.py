import os
from typing import Any

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from database import Base, SessionLocal, engine
from models import Request
from knowledge.search import search_chunks
import json

from ai.analyzer import analyze_request

import logging
import uuid

from fastapi import Depends, FastAPI, HTTPException, Request as FastAPIRequest
from fastapi.responses import HTMLResponse, JSONResponse

Base.metadata.create_all(bind=engine)

app = FastAPI()
security = HTTPBearer()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("request-analyzer")

JWT_CLAIM_NAME_IDENTIFIER = "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier"
JWT_CLAIM_NAME = "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name"

class SearchRequest(BaseModel):
    query: str

@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: FastAPIRequest,
    exc: Exception,
):
    logger.exception(
        "Unhandled exception: %s %s",
        request.method,
        request.url.path,
    )

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error"
        },
    )


@app.post("/knowledge/search")
def knowledge_search(data: SearchRequest):

    results = search_chunks(
        data.query,
        limit=3
    )

    return {
        "results": results
    }

def get_jwt_settings() -> dict[str, str]:
    issuer = os.getenv("JWT_ISSUER")
    audience = os.getenv("JWT_AUDIENCE")
    algorithm = os.getenv("JWT_ALGORITHM")
    secret_key = os.getenv("JWT_SECRET_KEY")

    if not issuer or not audience or not algorithm or not secret_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT configuration is missing"
        )

    if algorithm != "HS256":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unsupported JWT algorithm"
        )

    return {
        "issuer": issuer,
        "audience": audience,
        "algorithm": algorithm,
        "secret_key": secret_key,
    }


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict[str, Any]:
    token = credentials.credentials
    settings = get_jwt_settings()

    try:
        header = jwt.get_unverified_header(token)
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid JWT") from exc

    if header.get("alg") != settings["algorithm"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid JWT algorithm")

    try:
        payload = jwt.decode(
            token,
            key=settings["secret_key"],
            algorithms=[settings["algorithm"]],
            issuer=settings["issuer"],
            audience=settings["audience"],
        )
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="JWT expired") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid JWT") from exc

    user_id = payload.get(JWT_CLAIM_NAME_IDENTIFIER)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="JWT user identifier not found"
        )

    username = payload.get(JWT_CLAIM_NAME)
    return {
        "user_id": user_id,
        "username": username,
    }


class RequestData(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    message: str = Field(min_length=1, max_length=5000)

class RequestCreate(BaseModel):
    name: str
    message: str
    text_length: int
    word_count: int
    category: str
    priority: str
    sentiment: str
    summary: str
    action: str

@app.post("/requests")
def create_request(data: RequestCreate):
    request = Request(
        name=data.name,
        message=data.message,
        text_length=data.text_length,
        word_count=data.word_count,
        category=data.category,
        priority=data.priority,
        sentiment=data.sentiment,
        summary=data.summary,
        action=data.action
    )

    db = SessionLocal()

    try:
        db.add(request)
        db.commit()
        db.refresh(request)

        logger.info(
            "Request saved successfully: id=%s",
            request.id,
        )

        return {
            "id": request.id,
            "status": "saved"
        }

    except Exception:
        db.rollback()

        logger.exception(
            "Failed to save request"
        )

        raise

    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
def root():
    return """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>Анализатор обращений</title>
    </head>
    <body>
        <h1>Анализатор обращений</h1>

        <form id="loginForm">
    <label>Имя пользователя:</label><br>
    <input type="text" id="username" required><br><br>

    <label>Пароль:</label><br>
    <input type="password" id="password" required><br><br>

    <button type="submit">Войти</button>
</form>

<div id="authStatus"></div>

        <form id="requestForm">
    <label>Имя:</label><br>
    <input type="text" id="name" required><br><br>

    <label>Обращение:</label><br>
    <textarea id="message" rows="6" cols="50" required></textarea><br><br>

    <button type="submit">Анализировать</button>
</form>

<div id="result"></div>

<script>
    let accessToken = null;

    document.getElementById("loginForm").addEventListener("submit", async function(event) {
        event.preventDefault();

        const response = await fetch("http://localhost:5054/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                username: document.getElementById("username").value,
                password: document.getElementById("password").value
            })
        });

        const authStatus = document.getElementById("authStatus");

        if (!response.ok) {
            accessToken = null;
            authStatus.textContent = "Ошибка входа";
            return;
        }

        const result = await response.json();
        accessToken = result.accessToken;
        authStatus.textContent = "Вход выполнен";
    });

    document.getElementById("requestForm").addEventListener("submit", async function(event) {
        event.preventDefault();

        const resultContainer = document.getElementById("result");

        if (!accessToken) {
            resultContainer.textContent = "Сначала войдите в систему";
            return;
        }

        const name = document.getElementById("name").value;
        const message = document.getElementById("message").value;

        const response = await fetch("http://localhost:5678/webhook/request-analyzer", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${accessToken}`
            },
            body: JSON.stringify({
                name: name,
                message: message
            })
        });

        const result = await response.json();

        resultContainer.replaceChildren();

        const resultTitle = document.createElement("h2");
        resultTitle.textContent = "Результат анализа";
        resultContainer.appendChild(resultTitle);

        function appendLabeledParagraph(label, value) {
            const paragraph = document.createElement("p");
            const labelElement = document.createElement("strong");

            labelElement.textContent = `${label}:`;
            paragraph.append(labelElement, document.createTextNode(` ${value}`));
            resultContainer.appendChild(paragraph);
        }

        appendLabeledParagraph("Категория", result.category);
        appendLabeledParagraph("Приоритет", result.priority);
        appendLabeledParagraph("Тональность", result.sentiment);

        const summaryTitle = document.createElement("h3");
        summaryTitle.textContent = "Резюме";
        resultContainer.appendChild(summaryTitle);

        const summary = document.createElement("p");
        summary.textContent = result.summary;
        resultContainer.appendChild(summary);

        const actionTitle = document.createElement("h3");
        actionTitle.textContent = "Действие";
        resultContainer.appendChild(actionTitle);

        const action = document.createElement("p");
        action.textContent = result.action;
        resultContainer.appendChild(action);

        const originalRequestTitle = document.createElement("h3");
        originalRequestTitle.textContent = "Исходное обращение";
        resultContainer.appendChild(originalRequestTitle);

        const originalRequest = document.createElement("p");
        const originalName = document.createElement("strong");

        originalName.textContent = result.name;
        originalRequest.append(originalName, document.createTextNode(`: ${result.message}`));
        resultContainer.appendChild(originalRequest);
    });
</script>
    </body>
    </html>
    """

@app.get("/requests")
def get_requests(current_user: dict[str, Any] = Depends(get_current_user)):
    del current_user

    db = SessionLocal()

    try:
        requests = db.query(Request).order_by(Request.id.desc()).all()

        return [
            {
                "id": request.id,
                "created_at": request.created_at,
                "name": request.name,
                "message": request.message,
                "text_length": request.text_length,
                "word_count": request.word_count,
                "category": request.category,
                "priority": request.priority,
                "sentiment": request.sentiment,
                "summary": request.summary,
                "action": request.action
            }
            for request in requests
        ]

    finally:
        db.close()

@app.get("/requests-page", response_class=HTMLResponse)
def requests_page():
    return """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>История обращений</title>

        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 1200px;
                margin: 40px auto;
                padding: 0 20px;
                background: #f5f5f5;
            }

            h1 {
                margin-bottom: 30px;
            }

            .request {
                background: white;
                border-radius: 10px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            }

            .header {
                display: flex;
                justify-content: space-between;
                margin-bottom: 15px;
            }

            .name {
                font-weight: bold;
                font-size: 18px;
            }

            .date {
                color: #777;
            }

            .meta {
                display: flex;
                gap: 10px;
                margin: 10px 0;
            }

            .tag {
                background: #eee;
                padding: 5px 10px;
                border-radius: 5px;
            }

            .message {
                margin: 15px 0;
            }

            .label {
                font-weight: bold;
            }

            .empty {
                text-align: center;
                color: #777;
                padding: 40px;
            }
        </style>
    </head>

    <body>

        <h1>История обращений</h1>

        <form id="loginForm">
            <label>Имя пользователя:</label><br>
            <input type="text" id="username" required><br><br>

            <label>Пароль:</label><br>
            <input type="password" id="password" required><br><br>

            <button type="submit">Войти</button>
        </form>

        <div id="authStatus"></div>

        <div id="requests">
            Загрузка...
        </div>

        <script>
            let accessToken = null;

            document.getElementById("loginForm").addEventListener("submit", async function(event) {
                event.preventDefault();

                const response = await fetch("http://localhost:5054/login", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        username: document.getElementById("username").value,
                        password: document.getElementById("password").value
                    })
                });

                const authStatus = document.getElementById("authStatus");

                if (!response.ok) {
                    accessToken = null;
                    authStatus.textContent = "Ошибка входа";
                    return;
                }

                const result = await response.json();
                accessToken = result.accessToken;
                authStatus.textContent = "Вход выполнен";
                await loadRequests();
            });

            async function loadRequests() {
                const container = document.getElementById("requests");

                if (!accessToken) {
                    container.textContent = "Сначала войдите в систему";
                    return;
                }

                const response = await fetch("/requests", {
                    headers: {
                        "Authorization": `Bearer ${accessToken}`
                    }
                });

                if (!response.ok) {
                    container.textContent = "Не удалось загрузить историю обращений";
                    return;
                }

                const requests = await response.json();

                if (requests.length === 0) {
                    container.innerHTML = `
                        <div class="empty">
                            Обращений пока нет
                        </div>
                    `;
                    return;
                }

                container.replaceChildren();

                function createTag(label, value) {
                    const tag = document.createElement("span");
                    tag.className = "tag";
                    tag.textContent = `${label}: ${value}`;
                    return tag;
                }

                function createLabeledBlock(label, value, className) {
                    const block = document.createElement("div");
                    const labelElement = document.createElement("span");

                    if (className) {
                        block.className = className;
                    }

                    labelElement.className = "label";
                    labelElement.textContent = `${label}:`;
                    block.append(labelElement, document.createTextNode(` ${value}`));
                    return block;
                }

                requests.forEach(request => {
                    const card = document.createElement("div");
                    card.className = "request";

                    const header = document.createElement("div");
                    header.className = "header";

                    const name = document.createElement("div");
                    name.className = "name";
                    name.textContent = request.name;

                    const date = document.createElement("div");
                    date.className = "date";
                    date.textContent = new Date(request.created_at).toLocaleString("ru-RU");

                    header.append(name, date);

                    const meta = document.createElement("div");
                    meta.className = "meta";
                    meta.append(
                        createTag("Категория", request.category),
                        createTag("Приоритет", request.priority),
                        createTag("Тональность", request.sentiment)
                    );

                    const message = createLabeledBlock("Обращение", request.message, "message");
                    const summary = createLabeledBlock("Резюме", request.summary);
                    const action = createLabeledBlock("Рекомендуемое действие", request.action);
                    const separator = document.createElement("br");

                    card.append(header, meta, message, summary, separator, action);
                    container.appendChild(card);
                });
            }

            loadRequests();
        </script>

    </body>
    </html>
    """
@app.post("/analyze-request")
def analyze_request_endpoint(data: RequestData):

    name = data.name.strip()
    message = data.message.strip()

    if not name:
        raise HTTPException(
            status_code=422,
            detail="Name is empty"
        )

    if not message:
        raise HTTPException(
            status_code=422,
            detail="Message is empty"
        )

    logger.info(
        "Analysis started: name=%s, message_length=%s",
        name,
        len(message),
    )

    try:
        results = search_chunks(
            message,
            limit=3
        )

        logger.info(
            "RAG retrieval completed: chunks=%s",
            len(results),
        )

        context = "\n\n".join(
            item["content"]
            for item in results
        )

        ai_result = analyze_request(
            name,
            message,
            context
        )

        logger.info("LLM analysis completed")

        result = json.loads(ai_result)

        logger.info("Analysis result parsed successfully")

        return {
            "name": name,
            "message": message,
            **result
        }

    except json.JSONDecodeError:
        logger.exception(
            "LLM returned invalid JSON"
        )
        raise HTTPException(
            status_code=502,
            detail="AI service returned invalid response"
        )

    except Exception:
        logger.exception(
            "Analysis failed"
        )
        raise
    
