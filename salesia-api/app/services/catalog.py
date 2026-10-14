"""Motor de cotización de infraestructura AWS para los combos.

Dos modos:
- ``simulation``: usa las tarifas almacenadas en ``aws_rates`` × ``price_factor``
  de la región (idéntico a CloudCalc).
- ``live``: consulta la AWS Price List API (solo lectura) para EC2, RDS, S3,
  Lambda, Route 53 y CloudFront; usa el modo simulado como respaldo para
  DynamoDB y SNS o si AWS no está disponible.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.aws import pricing
from app.config import settings
from app.schemas.aws import (
    CatalogMeta,
    ComponentQuote,
    QuoteLine,
    QuoteResponse,
    RegionOut,
    ServiceOut,
)

DEFAULT_REGION = "us-east-1"
QUOTE_PER_MONTH_HOURS = 730.0

_SERVICE_NAMES = {
    "ec2": "Amazon EC2",
    "rds": "Amazon RDS",
    "s3": "Amazon S3",
    "lambda": "AWS Lambda",
    "dynamodb": "Amazon DynamoDB",
    "sns": "Amazon SNS",
    "cloudfront": "Amazon CloudFront",
    "route53": "Amazon Route 53",
}


def load_settings(db: Session) -> dict[str, str]:
    rows = db.execute(text("select key, value from app_settings")).mappings().all()
    return {row["key"]: row["value"] for row in rows}


def load_fx_rates(db: Session) -> dict[str, float]:
    rows = (
        db.execute(text("select currency, per_usd from aws_fx_rates"))
        .mappings()
        .all()
    )
    return {row["currency"]: float(row["per_usd"]) for row in rows}


def load_regions(db: Session) -> dict[str, dict[str, Any]]:
    rows = (
        db.execute(
            text(
                "select code, name, city, country, lat, lng, price_factor "
                "from aws_regions"
            )
        )
        .mappings()
        .all()
    )
    return {
        row["code"]: {
            "code": row["code"],
            "name": row["name"],
            "city": row["city"],
            "country": row["country"],
            "lat": float(row["lat"]) if row["lat"] is not None else None,
            "lng": float(row["lng"]) if row["lng"] is not None else None,
            "factor": float(row["price_factor"]),
        }
        for row in rows
    }


def load_rates(db: Session) -> dict[str, dict[str, dict[str, Any]]]:
    rows = (
        db.execute(
            text(
                "select service_code, rate_key, label, unit, value, attributes "
                "from aws_rates"
            )
        )
        .mappings()
        .all()
    )
    rates: dict[str, dict[str, dict[str, Any]]] = {}
    for row in rows:
        rates.setdefault(row["service_code"], {})[row["rate_key"]] = {
            "label": row["label"],
            "unit": row["unit"],
            "value": float(row["value"]),
            "attributes": row["attributes"] or {},
        }
    return rates


def effective_mode(db: Session, stored_settings: dict[str, str] | None = None) -> str:
    if stored_settings is None:
        stored_settings = load_settings(db)
    return stored_settings.get("catalog_mode") or settings.catalog_mode


def catalog_meta(db: Session) -> CatalogMeta:
    stored = load_settings(db)
    regions = load_regions(db)
    rates = load_rates(db)
    service_count = len([code for code in rates if code in _SERVICE_NAMES])
    return CatalogMeta(
        mode=effective_mode(db, stored),
        notice=stored.get("catalog_notice", ""),
        reference_date=stored.get("catalog_reference_date", ""),
        igv=float(stored.get("igv", "0.18")),
        service_count=service_count,
        region_count=len(regions),
        fx_rates=load_fx_rates(db),
    )


def list_regions(db: Session) -> list[RegionOut]:
    regions = load_regions(db)
    return [
        RegionOut(
            code=region["code"],
            name=region["name"],
            city=region["city"],
            country=region["country"],
            lat=region["lat"],
            lng=region["lng"],
            price_factor=region["factor"],
        )
        for region in sorted(regions.values(), key=lambda r: r["code"])
    ]


def list_services(db: Session) -> list[ServiceOut]:
    rows = (
        db.execute(
            text("select code, name, category, description from aws_services order by code")
        )
        .mappings()
        .all()
    )
    return [ServiceOut(**row) for row in rows]


def _rate(rates: dict, service: str, key: str, default: float | None = None) -> float | None:
    entry = rates.get(service, {}).get(key)
    if entry is None:
        return default
    return float(entry["value"])


def _rate_label(rates: dict, service: str, key: str, default: str) -> str:
    entry = rates.get(service, {}).get(key)
    return entry["label"] if entry else default


def _num(params: dict[str, Any], key: str, default: float) -> float:
    value = params.get(key, default)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return float(default)
    return float(value) if value >= 0 else float(default)


def _str(params: dict[str, Any], key: str, default: str) -> str:
    value = params.get(key, default)
    return value if isinstance(value, str) and value else default


def _round2(value: float) -> float:
    return round(value, 2)


def _simulation_component(
    rates: dict,
    service_code: str,
    params: dict[str, Any],
    factor: float,
) -> tuple[float, list[QuoteLine]] | None:
    if service_code == "ec2":
        instance_type = _str(params, "instanceType", "")
        base = _rate(rates, "ec2", f"type:{instance_type}")
        if base is None:
            return None
        os_key = _str(params, "os", "linux")
        os_mult = _rate(rates, "ec2", f"os:{os_key}", 1.0) or 1.0
        hours = _num(params, "hoursPerMonth", _rate(rates, "ec2", "config:monthly_hours", 730.0) or 730.0)
        count = _num(params, "instanceCount", 1)
        label = _rate_label(rates, "ec2", f"type:{instance_type}", instance_type)
        monthly = _round2(base * os_mult * factor * hours * count)
        return monthly, [QuoteLine(label=f"{label} ({os_key}) × {count:g}", amount=monthly)]

    if service_code == "rds":
        instance_type = _str(params, "instanceType", "")
        base = _rate(rates, "rds", f"type:{instance_type}")
        if base is None:
            return None
        engine = _str(params, "engine", "postgresql")
        multi_az = params.get("multiAz") is True
        storage_gb = _num(params, "storageGb", 100)
        hours = _rate(rates, "rds", "config:monthly_hours", 730.0) or 730.0
        multi_factor = _rate(rates, "rds", "config:multi_az_factor", 2.0) or 2.0
        gp3 = _rate(rates, "rds", "storage:gp3_gb_month", 0.115) or 0.115
        label = _rate_label(rates, "rds", f"type:{instance_type}", instance_type)
        instance = base * (multi_factor if multi_az else 1.0) * factor * hours
        storage = storage_gb * gp3 * factor
        monthly = _round2(instance + storage)
        az = "Multi-AZ" if multi_az else "Single-AZ"
        return monthly, [
            QuoteLine(label=f"{label} ({engine}, {az})", amount=_round2(instance)),
            QuoteLine(label=f"Almacenamiento {storage_gb:g} GB (gp3)", amount=_round2(storage)),
        ]

    if service_code == "s3":
        storage_class = _str(params, "storageClass", "standard")
        base = _rate(rates, "s3", f"class:{storage_class}")
        if base is None:
            return None
        storage_gb = _num(params, "storageGb", 1000)
        label = _rate_label(rates, "s3", f"class:{storage_class}", storage_class)
        monthly = _round2(storage_gb * base * factor)
        return monthly, [QuoteLine(label=f"{label} — {storage_gb:g} GB", amount=monthly)]

    if service_code == "lambda":
        requests_m = _num(params, "requestsMillions", 0)
        gb_seconds = _num(params, "gbSeconds", 0)
        req_rate = _rate(rates, "lambda", "request_per_million", 0.2) or 0.2
        gb_rate = _rate(rates, "lambda", "gb_second", 0.0000166667) or 0.0000166667
        request_cost = requests_m * req_rate * factor
        compute_cost = gb_seconds * gb_rate * factor
        monthly = _round2(request_cost + compute_cost)
        lines = [QuoteLine(label=f"{requests_m:g} M invocaciones", amount=_round2(request_cost))]
        if gb_seconds > 0:
            lines.append(QuoteLine(label=f"{gb_seconds:g} GB-segundo", amount=_round2(compute_cost)))
        return monthly, lines

    if service_code == "dynamodb":
        storage_gb = _num(params, "storageGb", 100)
        rcu = _num(params, "readCapacityUnits", 5)
        wcu = _num(params, "writeCapacityUnits", 5)
        storage_rate = _rate(rates, "dynamodb", "storage_gb_month", 0.25) or 0.25
        rcu_rate = _rate(rates, "dynamodb", "rcu_hour", 0.000013) or 0.000013
        wcu_rate = _rate(rates, "dynamodb", "wcu_hour", 0.000065) or 0.000065
        storage = storage_gb * storage_rate * factor
        read = rcu * QUOTE_PER_MONTH_HOURS * rcu_rate * factor
        write = wcu * QUOTE_PER_MONTH_HOURS * wcu_rate * factor
        monthly = _round2(storage + read + write)
        return monthly, [
            QuoteLine(label=f"Almacenamiento {storage_gb:g} GB", amount=_round2(storage)),
            QuoteLine(label=f"{rcu:g} RCU", amount=_round2(read)),
            QuoteLine(label=f"{wcu:g} WCU", amount=_round2(write)),
        ]

    if service_code == "sns":
        requests_m = _num(params, "requestsMillions", 1)
        rate = _rate(rates, "sns", "request_per_million", 0.5) or 0.5
        monthly = _round2(requests_m * rate * factor)
        return monthly, [QuoteLine(label=f"{requests_m:g} M publicaciones", amount=monthly)]

    if service_code == "cloudfront":
        data_out_gb = _num(params, "dataOutGb", 100)
        rate = _rate(rates, "cloudfront", "data_out_gb", 0.085) or 0.085
        monthly = _round2(data_out_gb * rate * factor)
        return monthly, [QuoteLine(label=f"{data_out_gb:g} GB de salida", amount=monthly)]

    if service_code == "route53":
        zones = _num(params, "zones", 1)
        queries_m = _num(params, "queriesMillions", 0)
        zone_rate = _rate(rates, "route53", "hosted_zone_month", 0.5) or 0.5
        query_rate = _rate(rates, "route53", "query_per_million", 0.4) or 0.4
        zone_cost = zones * zone_rate * factor
        query_cost = queries_m * query_rate * factor
        monthly = _round2(zone_cost + query_cost)
        lines = [QuoteLine(label=f"{zones:g} zona(s) hospedada(s)", amount=_round2(zone_cost))]
        if queries_m > 0:
            lines.append(QuoteLine(label=f"{queries_m:g} M consultas", amount=_round2(query_cost)))
        return monthly, lines

    return None


def _live_component(
    service_code: str,
    params: dict[str, Any],
    region_code: str,
    region_name: str,
) -> tuple[float, list[QuoteLine]] | None:
    location = pricing.location_for(region_code, region_name)
    try:
        if service_code == "ec2":
            instance_type = _str(params, "instanceType", "")
            os_key = _str(params, "os", "linux")
            price = pricing.ec2_hourly(instance_type, os_key, location)
            if price is None:
                return None
            hours = _num(params, "hoursPerMonth", 730.0)
            count = _num(params, "instanceCount", 1)
            monthly = _round2(price * hours * count)
            return monthly, [QuoteLine(label=f"{instance_type} ({os_key}) × {count:g}", amount=monthly)]

        if service_code == "rds":
            instance_type = _str(params, "instanceType", "")
            engine = _str(params, "engine", "postgresql")
            multi_az = params.get("multiAz") is True
            storage_gb = _num(params, "storageGb", 100)
            instance_price = pricing.rds_hourly(instance_type, engine, multi_az, location)
            storage_price = pricing.rds_storage_gb(location, multi_az)
            if instance_price is None or storage_price is None:
                return None
            instance = instance_price * 730.0
            storage = storage_gb * storage_price
            monthly = _round2(instance + storage)
            az = "Multi-AZ" if multi_az else "Single-AZ"
            return monthly, [
                QuoteLine(label=f"{instance_type} ({engine}, {az})", amount=_round2(instance)),
                QuoteLine(label=f"Almacenamiento {storage_gb:g} GB (gp3)", amount=_round2(storage)),
            ]

        if service_code == "s3":
            storage_class = _str(params, "storageClass", "standard")
            price = pricing.s3_gb(storage_class, location)
            if price is None:
                return None
            storage_gb = _num(params, "storageGb", 1000)
            monthly = _round2(storage_gb * price)
            return monthly, [QuoteLine(label=f"S3 {storage_class} — {storage_gb:g} GB", amount=monthly)]

        if service_code == "lambda":
            requests_m = _num(params, "requestsMillions", 0)
            gb_seconds = _num(params, "gbSeconds", 0)
            req_rate = pricing.lambda_request_million(location)
            gb_rate = pricing.lambda_gb_second(location)
            if req_rate is None or gb_rate is None:
                return None
            request_cost = requests_m * req_rate
            compute_cost = gb_seconds * gb_rate
            monthly = _round2(request_cost + compute_cost)
            lines = [QuoteLine(label=f"{requests_m:g} M invocaciones", amount=_round2(request_cost))]
            if gb_seconds > 0:
                lines.append(QuoteLine(label=f"{gb_seconds:g} GB-segundo", amount=_round2(compute_cost)))
            return monthly, lines

        if service_code == "cloudfront":
            price = pricing.cloudfront_gb(region_code)
            if price is None:
                return None
            data_out_gb = _num(params, "dataOutGb", 100)
            monthly = _round2(data_out_gb * price)
            return monthly, [QuoteLine(label=f"{data_out_gb:g} GB de salida", amount=monthly)]

        if service_code == "route53":
            zones = _num(params, "zones", 1)
            queries_m = _num(params, "queriesMillions", 0)
            zone_rate = pricing.route53_zone_month()
            if zone_rate is None:
                return None
            query_rate = pricing.route53_query_million(location) or 0.0
            zone_cost = zones * zone_rate
            query_cost = queries_m * query_rate
            monthly = _round2(zone_cost + query_cost)
            lines = [QuoteLine(label=f"{zones:g} zona(s) hospedada(s)", amount=_round2(zone_cost))]
            if queries_m > 0:
                lines.append(QuoteLine(label=f"{queries_m:g} M consultas", amount=_round2(query_cost)))
            return monthly, lines
    except pricing.PricingUnavailable:
        return None
    return None


def _quote_component(
    rates: dict,
    service_code: str,
    params: dict[str, Any],
    region: dict[str, Any],
    mode: str,
) -> ComponentQuote | None:
    name = _SERVICE_NAMES.get(service_code, service_code)
    if mode == "live" and pricing.is_configured():
        live = _live_component(service_code, params, region["code"], region["name"])
        if live is not None:
            monthly, breakdown = live
            return ComponentQuote(
                service_code=service_code,
                name=name,
                source="live",
                monthly_usd=monthly,
                breakdown=breakdown,
            )

    simulated = _simulation_component(rates, service_code, params, region["factor"])
    if simulated is None:
        return None
    monthly, breakdown = simulated
    return ComponentQuote(
        service_code=service_code,
        name=name,
        source="stored",
        monthly_usd=monthly,
        breakdown=breakdown,
    )


def _region_of(regions: dict[str, dict[str, Any]], region_code: str | None) -> dict[str, Any]:
    if region_code and region_code in regions:
        return regions[region_code]
    return regions[DEFAULT_REGION]


def quote_components(
    db: Session,
    components: list[dict[str, Any]],
    region_code: str | None,
) -> QuoteResponse:
    stored = load_settings(db)
    rates = load_rates(db)
    regions = load_regions(db)
    mode = effective_mode(db, stored)
    region = _region_of(regions, region_code)

    quotes: list[ComponentQuote] = []
    total = 0.0
    for component in components:
        quote = _quote_component(
            rates,
            component["service_code"],
            component.get("params") or {},
            region,
            mode,
        )
        if quote is None:
            continue
        quotes.append(quote)
        total += quote.monthly_usd

    pen_rate = load_fx_rates(db).get("PEN")
    return QuoteResponse(
        region_code=region["code"],
        region_name=region["name"],
        mode=mode,
        reference_date=stored.get("catalog_reference_date", ""),
        notice=stored.get("catalog_notice", ""),
        monthly_usd=_round2(total),
        monthly_pen=_round2(_round2(total) * pen_rate) if pen_rate else None,
        components=quotes,
    )


def plan_components_for(db: Session, plan_code: str) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    plan = (
        db.execute(
            text(
                "select id, code, name, region_code, monthly_price, setup_price "
                "from plans where code = :code and active = true"
            ),
            {"code": plan_code},
        )
        .mappings()
        .first()
    )
    if plan is None:
        return None, []

    rows = (
        db.execute(
            text(
                "select service_code, params from plan_components "
                "where plan_id = :plan_id order by service_code"
            ),
            {"plan_id": plan["id"]},
        )
        .mappings()
        .all()
    )
    components = [
        {"service_code": row["service_code"], "params": row["params"] or {}}
        for row in rows
    ]
    return dict(plan), components


def quote_plan(db: Session, plan_code: str, region_code: str | None = None) -> QuoteResponse | None:
    plan, components = plan_components_for(db, plan_code)
    if plan is None:
        return None
    effective_region = region_code or plan["region_code"]
    return quote_components(db, components, effective_region)
