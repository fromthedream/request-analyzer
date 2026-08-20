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

        const resultContainer = document.getElementById("result");
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
