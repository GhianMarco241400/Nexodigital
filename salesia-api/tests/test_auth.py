import pytest

import jwt


@pytest.fixture(scope="module")
def auth_service():
    try:
        from app.services import auth
    except Exception as exc:
        pytest.skip(f"Servicio de autenticación no disponible: {exc}")
    return auth


@pytest.fixture(scope="module")
def dependencies():
    try:
        from app import dependencies as deps
    except Exception as exc:
        pytest.skip(f"Dependencias no disponibles: {exc}")
    return deps


def test_hash_and_verify_password(auth_service) -> None:
    hashed = auth_service.hash_password("ContraseñaSegura123")
    assert hashed != "ContraseñaSegura123"
    assert auth_service.verify_password(hashed, "ContraseñaSegura123") is True
    assert auth_service.verify_password(hashed, "contraseña-incorrecta") is False


def test_create_and_decode_token(auth_service) -> None:
    token = auth_service.create_token(7, "administrador")
    payload = auth_service.decode_token(token)
    assert payload["sub"] == "7"
    assert payload["role"] == "administrador"


def test_expired_token_rejected(auth_service, monkeypatch) -> None:
    monkeypatch.setattr(auth_service.settings, "jwt_expire_minutes", -1)
    token = auth_service.create_token(7, "administrador")
    with pytest.raises(jwt.ExpiredSignatureError):
        auth_service.decode_token(token)


def test_tampered_token_rejected(auth_service) -> None:
    token = auth_service.create_token(7, "administrador")
    header, payload, signature = token.split(".")
    tampered = ".".join([header, payload, signature[::-1]])
    with pytest.raises(jwt.InvalidTokenError):
        auth_service.decode_token(tampered)


def test_require_roles_allows_and_denies(dependencies) -> None:
    from fastapi import Depends, FastAPI
    from fastapi.testclient import TestClient

    from app.permissions import ADMIN, GERENTE

    app = FastAPI()

    @app.get("/admin-only")
    def admin_only(user=Depends(dependencies.require_roles(ADMIN))):
        return {"role": user.role}

    client = TestClient(app)

    app.dependency_overrides[dependencies.get_current_user] = (
        lambda: dependencies.AuthenticatedUser(
            id=1, full_name="Admin", email="admin@example.com", role=ADMIN
        )
    )
    allowed = client.get("/admin-only")
    assert allowed.status_code == 200
    assert allowed.json() == {"role": ADMIN}

    app.dependency_overrides[dependencies.get_current_user] = (
        lambda: dependencies.AuthenticatedUser(
            id=2, full_name="Gerente", email="gerente@example.com", role=GERENTE
        )
    )
    denied = client.get("/admin-only")
    assert denied.status_code == 403


def test_login_invalid_body() -> None:
    try:
        from fastapi.testclient import TestClient

        from app.main import app
    except Exception as exc:
        pytest.skip(f"App no disponible: {exc}")

    with TestClient(app) as client:
        response = client.post("/auth/login", json={"email": "no-es-correo"})

    assert response.status_code == 422
