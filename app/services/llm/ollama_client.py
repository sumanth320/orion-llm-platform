import requests
from app.core.config import OLLAMA_URL


def generate_response(messages: list):
    payload = {
        "model": "llama3:latest",
        "messages": messages,
        "stream": False
    }

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=120
    )

    response.raise_for_status()

    data = response.json()

    return data["message"]["content"]