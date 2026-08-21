import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))

from fastapi.testclient import TestClient
from main import app


client = TestClient(app)

TEST_SECRET = "test-secret-key"
CLAIM_NAME_IDENTIFIER = "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier"
CLAIM_NAME = "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name"


def make_token(*, expired=False, issuer="AuthApi", audience="AuthApiClient", secret=TEST_SECRET, user_id="user-123", username="test-user"):
    now = datetime.now(timezone.utc)
    payload = {
        "iss": issuer,
        "aud": audience,
        "exp": (now - timedelta(minutes=1)).timestamp() if expired else (now + timedelta(hours=1)).timestamp(),
        "iat": int(now.timestamp()),
        CLAIM_NAME_IDENTIFIER: user_id,
        CLAIM_NAME: username,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


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

#история обращений требует корректный JWT
def test_get_requests_requires_auth():
    response = client.get("/requests")

    assert response.status_code == 401

#история обращений отклоняет неподписанный или некорректный токен
def test_get_requests_invalid_token():
    response = client.get("/requests", headers={"Authorization": "Bearer not-a-jwt"})

    assert response.status_code == 401

#история обращений требует корректный issuer/audience и срок жизни
def test_get_requests_valid_token():
    token = make_token()
    response = client.get("/requests", headers=auth_headers(token))

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

#некорректный issuer должен отклоняться
def test_get_requests_invalid_issuer():
    token = make_token(issuer="OtherIssuer")
    response = client.get("/requests", headers=auth_headers(token))

    assert response.status_code == 401

#некорректная audience должна отклоняться
def test_get_requests_invalid_audience():
    token = make_token(audience="OtherAudience")
    response = client.get("/requests", headers=auth_headers(token))

    assert response.status_code == 401

#просроченный токен должен отклоняться
def test_get_requests_expired_token():
    token = make_token(expired=True)
    response = client.get("/requests", headers=auth_headers(token))

    assert response.status_code == 401

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
            "summary": "Клиент не могу войти в личный кабинет",
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