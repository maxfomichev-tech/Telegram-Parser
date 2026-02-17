import os
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv

from utils import get_logger

load_dotenv()
logger = get_logger(__name__)

DEFAULT_MODEL = os.getenv("OPENROUTER_MODEL", "mistralai/mistral-7b-instruct:free")
DEFAULT_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")


class OpenRouterError(RuntimeError):
    """Raised when OpenRouter API responds with an error."""


def get_access_token() -> str:
    """
    Retrieve OpenRouter API key from environment.

    This adapts the original OAuth requirement for GigaChat
    to the simpler API-key auth used by OpenRouter.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise OpenRouterError("Не найден OPENROUTER_API_KEY в окружении или .env.")
    return api_key


def _post(url: str, headers: Dict[str, str], payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=60)
    except requests.RequestException as exc:
        raise OpenRouterError(f"Ошибка сети при обращении к OpenRouter: {exc}") from exc

    if not response.ok:
        raise OpenRouterError(
            f"OpenRouter вернул ошибку {response.status_code}: {response.text}"
        )

    try:
        return response.json()
    except ValueError as exc:
        raise OpenRouterError("Не удалось распарсить ответ OpenRouter как JSON") from exc


def generate_summary(text: str, *, model: Optional[str] = None) -> str:
    """
    Send text to OpenRouter chat/completions for summarization.
    """
    if not text or not text.strip():
        raise ValueError("Текст для суммаризации пуст.")

    api_key = get_access_token()
    chosen_model = model or DEFAULT_MODEL
    url = f"{DEFAULT_BASE_URL}/chat/completions"

    payload = {
        "model": chosen_model,
        "messages": [
            {
                "role": "system",
                "content": "Ты – ассистент, который делает краткие выжимки текста.",
            },
            {"role": "user", "content": text},
        ],
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://github.com",  # OpenRouter рекомендует указывать
        "X-Title": "CLI Summary Tool",
        "Content-Type": "application/json",
    }

    logger.info("Отправляю запрос в OpenRouter (модель: %s)...", chosen_model)
    data = _post(url, headers, payload)
    choice = data.get("choices", [{}])[0]
    message = choice.get("message", {})
    content = message.get("content")
    if not content:
        raise OpenRouterError("Не удалось получить ответ от модели.")
    logger.info("Суммаризация получена.")
    return content.strip()

