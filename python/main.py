from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
from database import engine, Base, SessionLocal
from models import Request

Base.metadata.create_all(bind=engine)

app = FastAPI()


class RequestData(BaseModel):
    name: str
    message: str

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

        return {
            "id": request.id,
            "status": "saved"
        }
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

        <form id="requestForm">
    <label>Имя:</label><br>
    <input type="text" id="name" required><br><br>

    <label>Обращение:</label><br>
    <textarea id="message" rows="6" cols="50" required></textarea><br><br>

    <button type="submit">Анализировать</button>
</form>

<div id="result"></div>

<script>
    document.getElementById("requestForm").addEventListener("submit", async function(event) {
        event.preventDefault();

        const name = document.getElementById("name").value;
        const message = document.getElementById("message").value;

        const response = await fetch("http://localhost:5678/webhook/request-analyzer", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                name: name,
                message: message
            })
        });

        const result = await response.json();

        document.getElementById("result").innerHTML = `
    <h2>Результат анализа</h2>

    <p><strong>Категория:</strong> ${result.category}</p>
    <p><strong>Приоритет:</strong> ${result.priority}</p>
    <p><strong>Тональность:</strong> ${result.sentiment}</p>

    <h3>Резюме</h3>
    <p>${result.summary}</p>

    <h3>Действие</h3>
    <p>${result.action}</p>

    <h3>Исходное обращение</h3>
    <p><strong>${result.name}</strong>: ${result.message}</p>
`;
    });
</script>
    </body>
    </html>
    """


@app.post("/analyze")
def analyze(data: RequestData):
    name = data.name.strip()
    message = data.message.strip()

    if not message:
        return {
            "valid": False,
            "data": None,
            "error": "Message is empty"
        }

    text_length = len(message)
    word_count = len(message.split())

    return {
        "valid": True,
        "data": {
            "name": name,
            "message": message,
            "text_length": text_length,
            "word_count": word_count
        }
    }
@app.get("/requests")
def get_requests():
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

        <div id="requests">
            Загрузка...
        </div>

        <script>
            async function loadRequests() {
                const response = await fetch("/requests");
                const requests = await response.json();

                const container = document.getElementById("requests");

                if (requests.length === 0) {
                    container.innerHTML = `
                        <div class="empty">
                            Обращений пока нет
                        </div>
                    `;
                    return;
                }

                container.innerHTML = requests.map(request => `
                    <div class="request">

                        <div class="header">
                            <div class="name">
                                ${request.name}
                            </div>

                            <div class="date">
                                ${new Date(request.created_at).toLocaleString("ru-RU")}
                            </div>
                        </div>

                        <div class="meta">
                            <span class="tag">
                                Категория: ${request.category}
                            </span>

                            <span class="tag">
                                Приоритет: ${request.priority}
                            </span>

                            <span class="tag">
                                Тональность: ${request.sentiment}
                            </span>
                        </div>

                        <div class="message">
                            <span class="label">Обращение:</span>
                            ${request.message}
                        </div>

                        <div>
                            <span class="label">Резюме:</span>
                            ${request.summary}
                        </div>

                        <br>

                        <div>
                            <span class="label">Рекомендуемое действие:</span>
                            ${request.action}
                        </div>

                    </div>
                `).join("");
            }

            loadRequests();
        </script>

    </body>
    </html>
    """
