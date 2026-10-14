import pytest

from app.services import catalog


def _app():
    try:
        from app.main import app
    except Exception as exc:
        pytest.skip(f"App no disponible: {exc}")
    return app


def _rates() -> dict:
    return {
        "ec2": {
            "type:t3.micro": {"label": "t3.micro", "unit": "USD/hora", "value": 0.0104, "attributes": {}},
            "os:linux": {"label": "Linux", "unit": "factor", "value": 1.0, "attributes": {}},
            "config:monthly_hours": {"label": "Horas", "unit": "horas", "value": 730.0, "attributes": {}},
        },
        "route53": {
            "hosted_zone_month": {"label": "Zona", "unit": "USD/mes", "value": 0.5, "attributes": {}},
            "query_per_million": {"label": "Consultas", "unit": "USD/millón", "value": 0.4, "attributes": {}},
        },
        "s3": {
            "class:standard": {"label": "S3 Standard", "unit": "USD/GB-mes", "value": 0.023, "attributes": {}},
        },
    }


def test_aws_routes_registered_and_public() -> None:
    paths = _app().openapi()["paths"]
    for route in ("/aws/catalog", "/aws/regions", "/aws/services"):
        assert route in paths
        assert "get" in paths[route]
        assert paths[route]["get"].get("security") in (None, [])
    assert "post" in paths["/aws/quote"]
    assert paths["/aws/quote"]["post"].get("security") in (None, [])


def test_quote_requires_plan_or_services() -> None:
    from fastapi.testclient import TestClient

    from app.db import get_db
    from app.main import app

    def _stub_db():
        yield None

    app.dependency_overrides[get_db] = _stub_db
    try:
        with TestClient(app) as client:
            response = client.post("/aws/quote", json={})
        assert response.status_code == 400
    finally:
        app.dependency_overrides.clear()


def test_simulation_ec2_matches_reference() -> None:
    monthly, lines = catalog._simulation_component(
        _rates(),
        "ec2",
        {"instanceType": "t3.micro", "os": "linux", "hoursPerMonth": 730, "instanceCount": 1},
        1.0,
    )
    assert monthly == pytest.approx(7.59)
    assert lines[0].amount == pytest.approx(7.59)


def test_simulation_route53_combines_zone_and_queries() -> None:
    monthly, lines = catalog._simulation_component(
        _rates(), "route53", {"zones": 1, "queriesMillions": 2}, 1.0
    )
    assert monthly == pytest.approx(1.3)
    assert len(lines) == 2


def test_simulation_region_factor_scales_price() -> None:
    monthly, _ = catalog._simulation_component(
        _rates(),
        "s3",
        {"storageGb": 100, "storageClass": "standard"},
        1.62,
    )
    assert monthly == pytest.approx(round(100 * 0.023 * 1.62, 2))
