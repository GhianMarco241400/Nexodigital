from decimal import Decimal
import json

from sqlalchemy import text
from sqlalchemy.engine import RowMapping
from sqlalchemy.orm import Session

from app.schemas.orders import ExtraSummary, OrderCreate, OrderCreated, PlanSummary
from app.services import catalog


class OrderBusinessError(Exception):
    """Violación de una regla de negocio; el router la traduce a HTTP 400."""


def create_order(db: Session, payload: OrderCreate) -> OrderCreated:
    if payload.plan_code == "a-medida":
        raise OrderBusinessError("El pedido a medida aún no está disponible")

    try:
        plan = (
            db.execute(
                text(
                    "select id, code, name, region_code, monthly_price, setup_price "
                    "from plans where code = :code and active = true"
                ),
                {"code": payload.plan_code},
            )
            .mappings()
            .first()
        )
        if plan is None:
            raise OrderBusinessError("El combo elegido no existe o no está disponible")

        extras = _load_extras(db, payload.extra_codes)

        monthly_total = Decimal(plan["monthly_price"])
        setup_total = Decimal(plan["setup_price"])
        for extra in extras:
            monthly_total += Decimal(extra["monthly_price"])
            setup_total += Decimal(extra["setup_price"])

        customer_id = _get_or_create_customer(db, payload)

        plan_region = payload.region_code or plan["region_code"]
        components, quote = _quote_infra(db, plan["id"], plan_region)
        region_code = quote.region_code
        infra_usd = Decimal(str(quote.monthly_usd))
        fx_rate = Decimal(str(catalog.load_fx_rates(db).get("PEN", 3.75)))
        infra_estimate = (infra_usd * fx_rate).quantize(Decimal("0.01"))

        order = (
            db.execute(
                text(
                    "insert into orders "
                    "(customer_id, plan_id, region_code, monthly_total, setup_total, "
                    "infra_usd, infra_estimate, fx_rate) "
                    "values (:customer_id, :plan_id, :region_code, "
                    ":monthly_total, :setup_total, :infra_usd, :infra_estimate, "
                    ":fx_rate) "
                    "returning id, code, status"
                ),
                {
                    "customer_id": customer_id,
                    "plan_id": plan["id"],
                    "region_code": region_code,
                    "monthly_total": monthly_total,
                    "setup_total": setup_total,
                    "infra_usd": infra_usd,
                    "infra_estimate": infra_estimate,
                    "fx_rate": fx_rate,
                },
            )
            .mappings()
            .one()
        )

        for component in components:
            db.execute(
                text(
                    "insert into order_components "
                    "(order_id, service_code, params, usd_monthly, breakdown) "
                    "values (:order_id, :service_code, cast(:params as jsonb), "
                    ":usd_monthly, cast(:breakdown as jsonb))"
                ),
                {
                    "order_id": order["id"],
                    "service_code": component["service_code"],
                    "params": json.dumps(component.get("params") or {}),
                    "usd_monthly": component.get("usd_monthly", 0),
                    "breakdown": json.dumps(component.get("breakdown") or []),
                },
            )

        for extra in extras:
            db.execute(
                text(
                    "insert into order_items "
                    "(order_id, extra_id, extra_name, monthly_price, setup_price, "
                    "quantity) "
                    "values (:order_id, :extra_id, :extra_name, :monthly_price, "
                    ":setup_price, 1)"
                ),
                {
                    "order_id": order["id"],
                    "extra_id": extra["id"],
                    "extra_name": extra["name"],
                    "monthly_price": extra["monthly_price"],
                    "setup_price": extra["setup_price"],
                },
            )

        db.execute(
            text(
                "insert into order_events "
                "(order_id, event_type, description, actor_id) "
                "values (:order_id, 'creado', "
                "'Pedido recibido desde la landing', :actor_id)"
            ),
            {"order_id": order["id"], "actor_id": None},
        )

        db.commit()
    except Exception:
        db.rollback()
        raise

    return OrderCreated(
        code=order["code"],
        status=order["status"],
        plan=PlanSummary(code=plan["code"], name=plan["name"]),
        extras=[
            ExtraSummary(code=extra["code"], name=extra["name"]) for extra in extras
        ],
        monthly_total=float(monthly_total),
        setup_total=float(setup_total),
    )


def _quote_infra(
    db: Session, plan_id: int, region_code: str
) -> tuple[list[dict], object]:
    rows = (
        db.execute(
            text(
                "select service_code, params from plan_components "
                "where plan_id = :plan_id order by service_code"
            ),
            {"plan_id": plan_id},
        )
        .mappings()
        .all()
    )
    components = [
        {"service_code": row["service_code"], "params": row["params"] or {}}
        for row in rows
    ]
    quote = catalog.quote_components(db, components, region_code)

    by_service = {component.service_code: component for component in quote.components}
    enriched: list[dict] = []
    for component in components:
        quoted = by_service.get(component["service_code"])
        if quoted is None:
            continue
        enriched.append(
            {
                "service_code": component["service_code"],
                "params": component["params"],
                "usd_monthly": quoted.monthly_usd,
                "breakdown": [line.model_dump() for line in quoted.breakdown],
            }
        )
    return enriched, quote


def _load_extras(db: Session, extra_codes: list[str]) -> list[RowMapping]:
    if not extra_codes:
        return []

    rows = (
        db.execute(
            text(
                "select id, code, name, monthly_price, setup_price "
                "from extras where code = any(:codes) and active = true"
            ),
            {"codes": extra_codes},
        )
        .mappings()
        .all()
    )
    by_code = {row["code"]: row for row in rows}

    extras: list[RowMapping] = []
    for code in extra_codes:
        if code not in by_code:
            raise OrderBusinessError(
                f"El extra '{code}' no existe o no está disponible"
            )
        extras.append(by_code[code])
    return extras


def _get_or_create_customer(db: Session, payload: OrderCreate) -> int:
    existing_id = db.execute(
        text("select id from customers where ruc = :ruc"),
        {"ruc": payload.ruc},
    ).scalar_one_or_none()
    if existing_id is not None:
        return existing_id

    created_id = db.execute(
        text(
            "insert into customers "
            "(company_name, ruc, contact_name, email, phone, region) "
            "values (:company_name, :ruc, :contact_name, :email, :phone, :region) "
            "on conflict (ruc) do nothing "
            "returning id"
        ),
        {
            "company_name": payload.company_name,
            "ruc": payload.ruc,
            "contact_name": payload.contact_name,
            "email": str(payload.email),
            "phone": payload.phone,
            "region": payload.region,
        },
    ).scalar_one_or_none()
    if created_id is not None:
        return created_id

    return db.execute(
        text("select id from customers where ruc = :ruc"),
        {"ruc": payload.ruc},
    ).scalar_one()
