import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))

from fastapi.testclient import TestClient
from main import app


client = TestClient(app)

#обращение реально сохраняется в БД
def test_create_request():
    response = client.post(
        "/requests",
        json={
            "name": "Антон",
            "message": "Не могу войти в личный кабинет",
            "text_length": 35,
            "word_count": 6,
            "category": "авторизация",
            "priority": "high",
            "sentiment": "negative",
            "summary": "Клиент не может войти в личный кабинет",
            "action": "Проверить учетную запись клиента"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "id" in data
    assert data["status"] == "saved"

#история обращений реально читается из БД
def test_get_requests():
    response = client.get("/requests")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) > 0

    request = data[0]

    assert "id" in request
    assert "name" in request
    assert "message" in request
    assert "category" in request
    assert "priority" in request
    assert "sentiment" in request

#/requests требует name
def test_create_request_missing_name():
    response = client.post(
        "/requests",
        json={
            "message": "Не могу войти в личный кабинет",
            "text_length": 35,
            "word_count": 6,
            "category": "авторизация",
            "priority": "high",
            "sentiment": "negative",
            "summary": "Клиент не может войти в личный кабинет",
            "action": "Проверить учетную запись клиента"
        }
    )

    assert response.status_code == 422

#/requests требует category
def test_create_request_missing_category():
    response = client.post(
        "/requests",
        json={
            "name": "Антон",
            "message": "Не могу войти в личный кабинет",
            "text_length": 35,
            "word_count": 6,
            "priority": "high",
            "sentiment": "negative",
            "summary": "Клиент не может войти в личный кабинет",
            "action": "Проверить учетную запись клиента"
        }
    )

    assert response.status_code == 422