import pytest

from app.services.review import (
    ReviewFeatures,
    assess,
    ruc_checksum_valid,
)


def _features(**overrides) -> ReviewFeatures:
    base = dict(
        plan_name="Negocio",
        monthly_total=100.0,
        setup_total=200.0,
        catalog_monthly=100.0,
        catalog_setup=200.0,
        infra_estimate=20.0,
        infra_usd=5.0,
        infra_ratio=0.2,
        ruc_valid=True,
        same_ruc_recent=0,
        disposable_email=False,
        phone_present=True,
        region_present=True,
        customer_orders=3,
        customer_confirmed=2,
    )
    base.update(overrides)
    return ReviewFeatures(**base)


def test_ruc_checksum_accepts_valid_ruc() -> None:
    assert ruc_checksum_valid("20131312955") is True


def test_ruc_checksum_rejects_wrong_digit() -> None:
    assert ruc_checksum_valid("20131312956") is False


def test_ruc_checksum_rejects_malformed() -> None:
    assert ruc_checksum_valid("123") is False
    assert ruc_checksum_valid("2013131295a") is False


def test_assess_clean_order_is_low_risk() -> None:
    verdict = assess(_features())
    assert verdict.risk == "bajo"
    assert verdict.recommendation == "aprobar"
    assert verdict.flags == []
    assert verdict.confidence >= 0.9


def test_assess_flags_high_risk_order() -> None:
    verdict = assess(
        _features(
            monthly_total=80.0,
            catalog_monthly=100.0,
            infra_estimate=60.0,
            infra_ratio=0.75,
            ruc_valid=False,
        )
    )
    assert verdict.risk == "alto"
    assert verdict.recommendation == "rechazar"
    codes = {flag.code for flag in verdict.flags}
    assert {"precio_inconsistente", "margen_critico", "ruc_invalido"} <= codes


def test_assess_flags_medium_risk_order() -> None:
    verdict = assess(
        _features(
            same_ruc_recent=3,
            disposable_email=True,
            customer_orders=5,
            customer_confirmed=0,
        )
    )
    assert verdict.risk == "medio"
    assert verdict.recommendation == "revisar"
    codes = {flag.code for flag in verdict.flags}
    assert {"duplicados", "email_desechable", "cliente_sin_confirmaciones"} <= codes


def test_llm_merge_replaces_summary_and_appends_flags(monkeypatch) -> None:
    from app.ai import provider as ai_provider
    from app.services import review

    monkeypatch.setattr(
        ai_provider,
        "complete_json",
        lambda **_kwargs: {
            "summary": "Resumen generado por el modelo.",
            "flags": [
                {"code": "llm_observacion", "severity": "medio", "message": "Detalle."},
                {"code": "invalido"},  # se ignora
            ],
        },
    )

    features = _features()
    merged = review._llm_merge(
        features, assess(features), provider="gemini", model="gemini-test"
    )
    assert merged.model == "gemini-test"
    codes = {flag.code for flag in merged.flags}
    assert "llm_observacion" in codes
    assert merged.risk == "medio"


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


def test_confirm_without_token_returns_401(api) -> None:
    _app, client = api
    assert client.post("/orders/PED-0001/confirm").status_code == 401


def test_confirm_forbidden_for_analista(api) -> None:
    app, client = api
    _login_as(app, "analista")
    assert client.post("/orders/PED-0001/confirm").status_code == 403


def test_reject_forbidden_for_gerente(api) -> None:
    app, client = api
    _login_as(app, "gerente")
    response = client.post("/orders/PED-0001/reject", json={"reason": "No aplica"})
    assert response.status_code == 403


def test_review_forbidden_for_almacen(api) -> None:
    app, client = api
    _login_as(app, "almacen")
    assert client.post("/orders/PED-0001/review").status_code == 403


def test_review_rejects_invalid_code(api) -> None:
    app, client = api
    _login_as(app, "administrador")
    assert client.post("/orders/abc/review").status_code == 422


def test_reject_requires_reason(api) -> None:
    app, client = api
    _login_as(app, "administrador")
    assert client.post("/orders/PED-0001/reject", json={}).status_code == 422
