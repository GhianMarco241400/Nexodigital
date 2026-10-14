import pytest


def test_health() -> None:
    try:
        from app.db import engine
        from app.main import app
    except Exception as exc:
        pytest.skip(f"App no disponible: {exc}")

    from fastapi.testclient import TestClient
    from sqlalchemy import text

    try:
        with engine.connect() as connection:
            connection.execute(text("select 1"))
    except Exception as exc:
        pytest.skip(f"Base de datos no disponible: {exc}")

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}
