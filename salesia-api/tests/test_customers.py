import pytest


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


def test_list_customers_without_token_returns_401(api) -> None:
    _app, client = api
    assert client.get("/customers").status_code == 401


def test_list_customers_forbidden_for_analista(api) -> None:
    app, client = api
    _login_as(app, "analista")
    assert client.get("/customers").status_code == 403


def test_list_customers_forbidden_for_almacen(api) -> None:
    app, client = api
    _login_as(app, "almacen")
    assert client.get("/customers").status_code == 403
