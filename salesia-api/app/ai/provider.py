from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.ai import gemini, openai_compat
from app.config import settings

PROVIDER_NAMES = ("gemini", "groq", "openrouter", "ollama", "openai")


@dataclass(frozen=True)
class ProviderSpec:
    name: str
    label: str
    kind: str  # "openai" (compatible) | "gemini"
    base_url: str
    key_attr: str | None
    model_attr: str
    requires_key: bool


PROVIDERS: dict[str, ProviderSpec] = {
    "gemini": ProviderSpec(
        "gemini", "Google Gemini", "gemini", "", "gemini_api_key", "gemini_model", True
    ),
    "groq": ProviderSpec(
        "groq",
        "Groq",
        "openai",
        "https://api.groq.com/openai/v1",
        "groq_api_key",
        "groq_model",
        True,
    ),
    "openrouter": ProviderSpec(
        "openrouter",
        "OpenRouter",
        "openai",
        "https://openrouter.ai/api/v1",
        "openrouter_api_key",
        "openrouter_model",
        True,
    ),
    "ollama": ProviderSpec(
        "ollama", "Ollama (local)", "openai", "", None, "ollama_model", False
    ),
    "openai": ProviderSpec(
        "openai", "OpenAI", "openai", "https://api.openai.com/v1", "openai_api_key",
        "openai_model", True,
    ),
}

_DEFAULT_PROVIDER = "gemini"


def normalize_provider(name: str | None) -> str:
    candidate = (name or "").strip().lower()
    return candidate if candidate in PROVIDERS else _DEFAULT_PROVIDER


def api_key(provider: str) -> str:
    spec = PROVIDERS[normalize_provider(provider)]
    if spec.key_attr is None:
        return ""
    return (getattr(settings, spec.key_attr, None) or "").strip()


def default_model(provider: str) -> str:
    spec = PROVIDERS[normalize_provider(provider)]
    return getattr(settings, spec.model_attr)


def base_url(provider: str) -> str:
    name = normalize_provider(provider)
    if name == "ollama":
        return settings.ollama_base_url.rstrip("/") + "/v1"
    return PROVIDERS[name].base_url


def has_key(provider: str) -> bool:
    spec = PROVIDERS[normalize_provider(provider)]
    return not spec.requires_key or bool(api_key(provider))


def complete_json(
    *,
    provider: str,
    system: str,
    user: str,
    model: str,
    timeout: float = 20.0,
) -> dict[str, Any] | None:
    """Despacha la petición JSON al proveedor configurado. None si no está listo."""
    name = normalize_provider(provider)
    spec = PROVIDERS[name]
    key = api_key(name)
    if spec.requires_key and not key:
        return None

    if spec.kind == "gemini":
        return gemini.complete_json(
            api_key=key, model=model, system=system, user=user, timeout=timeout
        )

    return openai_compat.complete_json(
        base_url=base_url(name),
        api_key=key or "ollama",
        model=model,
        system=system,
        user=user,
        timeout=timeout,
    )
