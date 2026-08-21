import os
import requests


OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://localhost:11434"
)


def create_embedding(text: str):

    response = requests.post(
        f"{OLLAMA_URL}/api/embed",
        json={
            "model": "nomic-embed-text",
            "input": text
        }
    )

    response.raise_for_status()

    return response.json()["embeddings"][0]