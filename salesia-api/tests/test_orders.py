import pytest

VALID_PAYLOAD = {
    "company_name": "Andes Café S.A.C.",
    "ruc": "20601234561",
    "contact_name": "Valeria Rojas",
    "email": "valeria@andescafe.example",
    "plan_code": "negocio",
}


@pytest.fixture()
def client():
    try:
        from fastapi.testclient import TestClient

        from app.main import app
    except Exception as exc:
        pytest.skip(f"App no disponible: {exc}")

    with TestClient(app) as test_client:
        yield test_client


def test_order_invalid_ruc(client) -> None:
    response = client.post("/orders", json={**VALID_PAYLOAD, "ruc": "123"})
    assert response.status_code == 422


def test_order_invalid_email(client) -> None:
    response = client.post("/orders", json={**VALID_PAYLOAD, "email": "no-es-correo"})
    assert response.status_code == 422


def test_order_missing_plan_code(client) -> None:
    payload = {key: value for key, value in VALID_PAYLOAD.items() if key != "plan_code"}
    response = client.post("/orders", json=payload)
    assert response.status_code == 422
