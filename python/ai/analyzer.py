import os
import requests


OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://host.docker.internal:11434"
)


def analyze_request(
    name: str,
    message: str,
    context: str
):

    prompt = f"""
Ты анализируешь обращения клиентов службы поддержки.

Используй базу знаний как дополнительный источник информации. 
Если база знаний не содержит ответа, классифицируй обращение по правилам ниже.

Верни строго JSON без markdown:

{{
  "category": "",
  "priority": "",
  "sentiment": "",
  "summary": "",
  "action": ""
}}

Правила:

- category — одна из:
  Technical Issue, Account, Payment, Security, Feature Request, General Question

  Правила выбора категории:

- Account:
  проблемы входа, пароля, регистрации, профиля пользователя, доступа к аккаунту.

- Payment:
  проблемы оплаты, списаний, транзакций, возвратов.

- Security:
  взлом, подозрительная активность, утечка данных, безопасность.

- Technical Issue:
  ошибки системы, баги, недоступность сервиса.

- Feature Request:
  запрос новых функций.

- General Question:
  общие вопросы, которые не относятся к другим категориям.

Если обращение связано со входом, паролем или доступом пользователя — всегда выбирай Account.

- priority — только:
  low, medium, high

- sentiment — только:
  positive, neutral, negative

- summary — краткое описание проблемы клиента одним предложением.

- action — конкретное действие сотрудника поддержки.
  Не используй название категории.
  Action должен начинаться с глагола:
  проверить, восстановить, уточнить, предоставить, зарегистрировать, передать.

Примеры правильного action:
"Проверить состояние аккаунта и данные авторизации"
"Проверить информацию о платеже"
"Восстановить доступ к аккаунту"

ВАЖНО:
- Отвечай только на русском языке.
- Поле action обязательно должно быть на русском языке.
- Action не должен быть названием категории.
- Action должен начинаться с глагола.

Примеры:
Проверить состояние аккаунта и данные авторизации.
Проверить информацию о платеже.
Восстановить доступ к аккаунту.

База знаний:

{context}

Клиент:
{name}

Обращение:
{message}
"""


    response = requests.post(
    f"{OLLAMA_URL}/api/generate",
    json={
        "model": "qwen3:8b",
        "prompt": prompt,
        "stream": False,
        "format": "json"
    },
    headers={
        "Content-Type": "application/json; charset=utf-8"
    }
)

    response.raise_for_status()

    response.encoding = "utf-8"

    return response.json()["response"]