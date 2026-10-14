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


def test_list_orders_without_token_returns_401(api) -> None:
    _app, client = api
    response = client.get("/orders")
    assert response.status_code == 401


def test_list_orders_forbidden_for_almacen(api) -> None:
    app, client = api
    _login_as(app, "almacen")
    assert client.get("/orders").status_code == 403


def test_list_orders_forbidden_for_analista(api) -> None:
    app, client = api
    _login_as(app, "analista")
    assert client.get("/orders").status_code == 403


def test_list_orders_rejects_page_size_over_limit(api) -> None:
    app, client = api
    _login_as(app, "administrador")
    assert client.get("/orders", params={"page_size": 1000}).status_code == 422


def test_list_orders_rejects_invalid_status(api) -> None:
    app, client = api
    _login_as(app, "administrador")
    assert client.get("/orders", params={"status": "otro"}).status_code == 422


def test_order_detail_rejects_invalid_code(api) -> None:
    app, client = api
    _login_as(app, "administrador")
    assert client.get("/orders/abc").status_code == 422
