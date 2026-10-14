"""Sincroniza las tarifas de referencia con la AWS Price List API (solo lectura).

Ejecuta únicamente llamadas de lectura (`pricing:GetProducts` y
`sts:GetCallerIdentity`). Nunca crea, modifica ni elimina recursos AWS.

Uso:
    python -m scripts.sync_aws_prices            # simulación (dry-run)
    python -m scripts.sync_aws_prices --apply    # escribe en aws_rates y
                                                 # activa catalog_mode=live
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone

from sqlalchemy import text

from app.aws import pricing
from app.db import SessionLocal

REFERENCE_REGION = "us-east-1"
REFERENCE_NAME = "US East (N. Virginia)"

_NOTE = "actualizado desde AWS Price List API (referencia us-east-1)"

_LIVE_NOTICE = (
    "Precios On-Demand obtenidos en vivo desde la AWS Price List API "
    "(región de referencia us-east-1, sin impuestos). No es una cotización "
    "oficial de AWS."
)
_SIM_NOTICE = (
    "Simulación académica con tarifas de referencia aproximadas. "
    "No es una cotización de AWS."
)


def _live_value(service_code: str, rate_key: str, location: str) -> float | None:
    try:
        if service_code == "ec2" and rate_key.startswith("type:"):
            return pricing.ec2_hourly(rate_key.removeprefix("type:"), "linux", location)
        if service_code == "rds" and rate_key.startswith("type:"):
            return pricing.rds_hourly(
                rate_key.removeprefix("type:"), "postgresql", False, location
            )
        if service_code == "rds" and rate_key == "storage:gp3_gb_month":
            return pricing.rds_storage_gb(location, False)
        if service_code == "s3" and rate_key == "class:standard":
            return pricing.s3_gb("standard", location)
        if service_code == "route53" and rate_key == "hosted_zone_month":
            return pricing.route53_zone_month()
        if service_code == "route53" and rate_key == "query_per_million":
            return pricing.route53_query_million(location)
        if service_code == "cloudfront" and rate_key == "data_out_gb":
            return pricing.cloudfront_gb(REFERENCE_REGION)
        if service_code == "lambda" and rate_key == "request_per_million":
            return pricing.lambda_request_million(location)
        if service_code == "lambda" and rate_key == "gb_second":
            return pricing.lambda_gb_second(location)
    except pricing.PricingUnavailable as exc:
        print(f"  ! {service_code}/{rate_key}: {exc}")
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="escribe en la base de datos")
    parser.add_argument(
        "--mode",
        choices=["live", "simulation"],
        default="live",
        help="valor de app_settings.catalog_mode al aplicar",
    )
    args = parser.parse_args()

    if not pricing.is_configured():
        print("No hay credenciales AWS configuradas (AWS_ACCESS_KEY_ID/SECRET).")
        return 1

    identity = pricing.verify_identity()
    print(f"Cuenta AWS: {identity.get('Account')}  ARN: {identity.get('Arn')}")
    print("(estas lecturas quedan registradas en CloudTrail)\n")

    location = pricing.location_for(REFERENCE_REGION, REFERENCE_NAME)

    with SessionLocal() as db:
        rows = (
            db.execute(
                text(
                    "select id, service_code, rate_key, value "
                    "from aws_rates order by service_code, rate_key"
                )
            )
            .mappings()
            .all()
        )

        changes: list[tuple[int, str, str, float]] = []
        for row in rows:
            live = _live_value(row["service_code"], row["rate_key"], location)
            if live is None:
                continue
            current = float(row["value"])
            marker = "==" if abs(current - live) < 1e-12 else "->"
            print(f"  {row['service_code']:10} {row['rate_key']:24} {current:>12.10g} {marker} {live:.10g}")
            if marker == "->":
                changes.append((row["id"], row["service_code"], row["rate_key"], live))

        print(f"\n{len(changes)} tarifa(s) por actualizar.")

        if not args.apply:
            print("Dry-run: usa --apply para escribir los cambios.")
            return 0

        for rate_id, _service, _key, live in changes:
            db.execute(
                text("update aws_rates set value = :value where id = :id"),
                {"value": live, "id": rate_id},
            )

        today = datetime.now(timezone.utc).date().isoformat()
        db.execute(
            text(
                "update app_settings set value = :value where key = 'catalog_mode'"
            ),
            {"value": args.mode},
        )
        db.execute(
            text(
                "update app_settings set value = :value "
                "where key = 'catalog_reference_date'"
            ),
            {"value": today},
        )
        notice = _LIVE_NOTICE if args.mode == "live" else _SIM_NOTICE
        db.execute(
            text("update app_settings set value = :value where key = 'catalog_notice'"),
            {"value": notice},
        )
        db.commit()
        print(f"Aplicado. catalog_mode='{args.mode}', referencia={today}.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
