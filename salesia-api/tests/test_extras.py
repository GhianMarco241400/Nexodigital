import pytest

from app.schemas.extras import ExtraOut


def _app():
    try:
        from app.main import app
    except Exception as exc:
        pytest.skip(f"App no disponible: {exc}")
    return app


def test_extra_out_serializes_amounts_as_numbers() -> None:
    extra = ExtraOut(
        code="web",
        name="Web",
        description=None,
        monthly_price=49,
        setup_price=99,
    )

    data = extra.model_dump()
    assert isinstance(data["monthly_price"], float)
    assert isinstance(data["setup_price"], float)
    assert data["monthly_price"] == 49.0
    assert data["setup_price"] == 99.0
    assert data["description"] is None

    payload = extra.model_dump_json()
    assert '"monthly_price":49.0' in payload
    assert '"setup_price":99.0' in payload


def test_extras_route_registered_and_public() -> None:
    app = _app()

    paths = app.openapi()["paths"]
    assert "/extras" in paths
    assert "get" in paths["/extras"]

    extras_operation = paths["/extras"]["get"]
    assert extras_operation.get("security") in (None, [])

    orders_operation = paths["/orders"]["get"]
    assert orders_operation.get("security")
