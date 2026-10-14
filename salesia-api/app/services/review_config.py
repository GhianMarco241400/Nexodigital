from __future__ import annotations

import time

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.ai import provider as ai_provider
from app.config import settings
from app.schemas.review_config import ReviewConfigOut, ReviewTestResult
from app.services.audit import write_audit

_ALLOWED_MODES = frozenset({"heuristic", "llm", "hybrid"})

_SETTING_KEY = "review_mode"
_MODE_KEY = "review_mode"
_PROVIDER_KEY = "review_provider"
_MODEL_KEY = "review_model"
_AUDIT_ACTION = "settings.review.update"

_NOTE_MODE = "Motor de revisión con IA: heuristic | llm | hybrid."
_NOTE_PROVIDER = "Proveedor de IA: gemini | groq | openrouter | ollama | openai."
_NOTE_MODEL = "Modelo de IA (vacío = el del proveedor)."


def _get_setting(db: Session | None, key: str) -> str | None:
    if db is None:
        return None
    return db.execute(
        text("select value from app_settings where key = :key"),
        {"key": key},
    ).scalar_one_or_none()


def _upsert(db: Session, key: str, value: str, note: str) -> None:
    db.execute(
        text(
            "insert into app_settings (key, value, note) values (:key, :value, :note) "
            "on conflict (key) do update set value = excluded.value, note = excluded.note"
        ),
        {"key": key, "value": value, "note": note},
    )


def get_review_mode(db: Session | None) -> str:
    """Modo efectivo: `app_settings.review_mode` con respaldo en `.env`."""
    mode = (_get_setting(db, _MODE_KEY) or settings.review_mode or "heuristic").strip().lower()
    return mode if mode in _ALLOWED_MODES else "heuristic"


def get_review_provider(db: Session | None) -> str:
    """Proveedor efectivo: `app_settings.review_provider` con respaldo en `.env`."""
    return ai_provider.normalize_provider(
        _get_setting(db, _PROVIDER_KEY) or settings.review_provider
    )


def get_review_model(db: Session | None, provider: str) -> str:
    """Modelo efectivo: `app_settings.review_model` o el default del proveedor."""
    stored = (_get_setting(db, _MODEL_KEY) or "").strip()
    return stored or ai_provider.default_model(provider)


def get_review_config(db: Session | None) -> ReviewConfigOut:
    mode = get_review_mode(db)
    provider = get_review_provider(db)
    model = get_review_model(db, provider)
    last = None
    if db is not None:
        last = (
            db.execute(
                text(
                    "select a.created_at, s.full_name as actor_name "
                    "from audit_log a "
                    "left join staff_users s on s.id = a.actor_id "
                    "where a.action = :action and a.entity = 'settings' "
                    "and a.entity_id = :entity_id "
                    "order by a.created_at desc, a.id desc limit 1"
                ),
                {"action": _AUDIT_ACTION, "entity_id": _SETTING_KEY},
            )
            .mappings()
            .first()
        )
    return ReviewConfigOut(
        mode=mode,
        provider=provider,
        model=model,
        ai_enabled=mode != "heuristic",
        has_api_key=ai_provider.has_key(provider),
        updated_by=last["actor_name"] if last else None,
        updated_at=last["created_at"] if last else None,
    )


def set_review_config(
    db: Session,
    *,
    mode: str | None = None,
    provider: str | None = None,
    model: str | None = None,
    actor_id: int | None = None,
) -> None:
    detail: dict[str, Any] = {}

    if mode is not None:
        normalized = mode.strip().lower()
        if normalized not in _ALLOWED_MODES:
            raise ValueError(f"Modo inválido: {mode}")
        _upsert(db, _MODE_KEY, normalized, _NOTE_MODE)
        detail["mode"] = normalized

    if provider is not None:
        candidate = provider.strip().lower()
        if candidate not in ai_provider.PROVIDERS:
            raise ValueError(f"Proveedor inválido: {provider}")
        _upsert(db, _PROVIDER_KEY, candidate, _NOTE_PROVIDER)
        detail["provider"] = candidate

    if model is not None:
        _upsert(db, _MODEL_KEY, model.strip(), _NOTE_MODEL)
        detail["model"] = model.strip()

    write_audit(
        db,
        action=_AUDIT_ACTION,
        entity="settings",
        entity_id=_SETTING_KEY,
        actor_id=actor_id,
        detail=detail or {"noop": True},
    )
    db.commit()


def set_review_mode(db: Session | None, *, mode: str, actor_id: int | None) -> None:
    """Compatibilidad: actualiza solo el modo."""
    set_review_config(db, mode=mode, actor_id=actor_id)


def test_provider(db: Session | None) -> ReviewTestResult:
    provider = get_review_provider(db)
    model = get_review_model(db, provider)
    if not ai_provider.has_key(provider):
        return ReviewTestResult(
            ok=False,
            provider=provider,
            model=model,
            error=(
                f"Falta la clave de {provider}. Configura la variable en el servidor "
                "(.env) y reinicia."
            ),
        )

    start = time.perf_counter()
    result = ai_provider.complete_json(
        provider=provider,
        system="Devuelves siempre un JSON válido.",
        user='Devuelve exactamente {"pong": true}',
        model=model,
    )
    latency_ms = int((time.perf_counter() - start) * 1000)

    if result is None:
        return ReviewTestResult(
            ok=False,
            provider=provider,
            model=model,
            latency_ms=latency_ms,
            error=f"{provider} no respondió (revisa la clave, la red o el saldo).",
        )
    return ReviewTestResult(ok=True, provider=provider, model=model, latency_ms=latency_ms)
