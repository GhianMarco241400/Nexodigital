from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Any

logger = logging.getLogger("salesia.ai.gemini")

_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


def complete_json(
    *,
    api_key: str,
    model: str,
    system: str,
    user: str,
    timeout: float = 20.0,
) -> dict[str, Any] | None:
    """Pide a Google Gemini una respuesta JSON (`generateContent`).

    Devuelve None si no está disponible. No registra la clave ni el contenido.
    """
    if not api_key:
        return None

    url = f"{_BASE}/{model}:generateContent?key={api_key}"
    body = json.dumps(
        {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.2,
            },
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
        logger.warning("Gemini no disponible: %s", exc.__class__.__name__)
        return None

    try:
        text = payload["candidates"][0]["content"]["parts"][0]["text"]
        parsed = json.loads(text)
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        logger.warning("Respuesta de Gemini inválida: %s", exc.__class__.__name__)
        return None

    return parsed if isinstance(parsed, dict) else None
