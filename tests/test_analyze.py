import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))

from fastapi.testclient import TestClient
from main import app


client = TestClient(app)

#/analyze корректно обрабатывает нормальное обращение
def test_analyze_valid_request():
    response = client.post(
        "/analyze",
        json={
            "name": "Антон",
            "message": "Не могу войти в личный кабинет"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["valid"] is True
    assert data["data"]["name"] == "Антон"
    assert data["data"]["message"] == "Не могу войти в личный кабинет"
    assert data["data"]["text_length"] == len("Не могу войти в личный кабинет")
    assert data["data"]["word_count"] == 6

#пустое сообщение отклоняется логикой
def test_analyze_empty_message():
    response = client.post(
        "/analyze",
        json={
            "name": "Антон",
            "message": "   "
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["valid"] is False
    assert data["data"] is None
    assert data["error"] == "Message is empty"

#FastAPI отклоняет запрос без message
def test_analyze_missing_message():
    response = client.post(
        "/analyze",
        json={
            "name": "Антон"
        }
    )

    assert response.status_code == 422

#FastAPI отклоняет запрос без name
def test_analyze_missing_name():
    response = client.post(
        "/analyze",
        json={
            "message": "Не могу войти в личный кабинет"
        }
    )

    assert response.status_code == 422
