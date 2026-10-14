from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Any

logger = logging.getLogger("salesia.ai.openai_compat")


def complete_json(
    *,
    base_url: str,
    api_key: str,
    model: str,
    system: str,
    user: str,
    timeout: float = 20.0,
) -> dict[str, Any] | None:
    """Cliente para APIs compatibles con OpenAI (`/chat/completions`).

    Sirve para OpenAI, Groq, OpenRouter y Ollama. Devuelve None si no está
    disponible. No registra la clave ni el contenido; sólo el tipo de error.
    """
    if not api_key:
        return None

    body = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        base_url.rstrip("/") + "/chat/completions",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
        logger.warning("Proveedor no disponible: %s", exc.__class__.__name__)
        return None

    try:
        content = payload["choices"][0]["message"]["content"]
        parsed = json.loads(content)
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        logger.warning("Respuesta inválida: %s", exc.__class__.__name__)
        return None

    return parsed if isinstance(parsed, dict) else None
