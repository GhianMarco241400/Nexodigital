import pytest

from app.services import review_config


class _FakeResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class _FakeDb:
    """Devuelve el valor por clave desde un dict (BD simulada)."""

    def __init__(self, values=None):
        self._values = values or {}

    def execute(self, _stmt, params=None, **_kwargs):
        key = (params or {}).get("key")
        return _FakeResult(self._values.get(key))


# --- modo -----------------------------------------------------------------


def test_get_review_mode_prefers_stored_value(monkeypatch) -> None:
    monkeypatch.setattr(review_config.settings, "review_mode", "llm", raising=False)
    assert review_config.get_review_mode(_FakeDb({"review_mode": "hybrid"})) == "hybrid"


def test_get_review_mode_falls_back_to_env(monkeypatch) -> None:
    monkeypatch.setattr(review_config.settings, "review_mode", "llm", raising=False)
    assert review_config.get_review_mode(_FakeDb()) == "llm"


def test_get_review_mode_rejects_unknown(monkeypatch) -> None:
    monkeypatch.setattr(review_config.settings, "review_mode", "llm", raising=False)
    assert review_config.get_review_mode(_FakeDb({"review_mode": "banana"})) == "heuristic"


# --- proveedor ------------------------------------------------------------


def test_get_review_provider_prefers_stored_value() -> None:
    assert review_config.get_review_provider(_FakeDb({"review_provider": "groq"})) == "groq"


def test_get_review_provider_falls_back_to_env(monkeypatch) -> None:
    monkeypatch.setattr(review_config.settings, "review_provider", "openrouter", raising=False)
    assert review_config.get_review_provider(_FakeDb()) == "openrouter"


def test_get_review_provider_rejects_unknown() -> None:
    assert review_config.get_review_provider(_FakeDb({"review_provider": "banana"})) == "gemini"


# --- modelo ---------------------------------------------------------------


def test_get_review_model_defaults_to_provider(monkeypatch) -> None:
    monkeypatch.setattr(review_config.settings, "gemini_model", "gemini-x", raising=False)
    assert review_config.get_review_model(_FakeDb(), "gemini") == "gemini-x"


def test_get_review_model_prefers_stored_value() -> None:
    db = _FakeDb({"review_model": "modelo-custom"})
    assert review_config.get_review_model(db, "gemini") == "modelo-custom"


# --- validación / test de conexión ----------------------------------------


def test_set_review_config_rejects_invalid_mode() -> None:
    with pytest.raises(ValueError):
        review_config.set_review_config(None, mode="banana", actor_id=None)


def test_set_review_mode_rejects_invalid() -> None:
    with pytest.raises(ValueError):
        review_config.set_review_mode(None, mode="banana", actor_id=None)


def test_set_review_config_rejects_invalid_provider() -> None:
    with pytest.raises(ValueError):
        review_config.set_review_config(None, provider="banana", actor_id=None)


def test_test_provider_without_key(monkeypatch) -> None:
    monkeypatch.setattr(review_config.settings, "gemini_api_key", None, raising=False)
    result = review_config.test_provider(_FakeDb())
    assert result.ok is False
    assert "gemini" in (result.error or "").lower()


# --- endpoints ------------------------------------------------------------


@pytest.fixture()
def api():
    try:
        from fastapi.testclient import TestClient

        from app.db import get_db
        from app.main import app
    except Exception as exc:
        pytest.skip(f"App no disponible: {exc}")

    def _stub_db():
        yield None

    app.dependency_overrides[get_db] = _stub_db
    with TestClient(app) as client:
        yield app, client
    app.dependency_overrides.clear()


def _login_as(app, role: str) -> None:
    from app.dependencies import AuthenticatedUser, get_current_user

    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        id=99, full_name="Usuario de prueba", email="test@example.com", role=role
    )


def test_review_config_requires_auth(api) -> None:
    _app, client = api
    assert client.get("/settings/review").status_code == 401
    assert client.put("/settings/review", json={"mode": "hybrid"}).status_code == 401


def test_review_config_forbidden_for_analista(api) -> None:
    app, client = api
    _login_as(app, "analista")
    assert client.put("/settings/review", json={"mode": "hybrid"}).status_code == 403


def test_review_config_rejects_invalid_mode(api) -> None:
    app, client = api
    _login_as(app, "administrador")
    assert client.put("/settings/review", json={"mode": "banana"}).status_code == 422


def test_review_config_rejects_invalid_provider(api) -> None:
    app, client = api
    _login_as(app, "administrador")
    response = client.put("/settings/review", json={"mode": "hybrid", "provider": "banana"})
    assert response.status_code == 422


def test_review_test_endpoint_with_admin(api, monkeypatch) -> None:
    app, client = api
    monkeypatch.setattr(review_config.settings, "gemini_api_key", "test-key", raising=False)
    monkeypatch.setattr(
        review_config.ai_provider, "complete_json", lambda **_kwargs: {"pong": True}
    )
    _login_as(app, "administrador")
    response = client.post("/settings/review/test")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["provider"] == "gemini"
    assert payload["latency_ms"] is not None
