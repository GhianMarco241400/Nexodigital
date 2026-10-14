"""Cliente de solo lectura para la AWS Price List Query API.

Expone funciones que devuelven el precio On-Demand real (en USD) de los
servicios que forman parte de los combos. Nunca crea ni modifica recursos AWS:
únicamente ejecuta `pricing:GetProducts`.

Las credenciales se resuelven desde `app.config.settings` o, si no están, desde
la cadena de credenciales por defecto de boto3 (variables de entorno / perfil).
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.config import settings
from app.aws.regions import cloudfront_edge_location, pricing_location

logger = logging.getLogger("salesia.aws.pricing")

PRICING_API_REGION = "us-east-1"
CACHE_TTL_SECONDS = 30 * 60

_OS_MAP: dict[str, str] = {
    "linux": "Linux",
    "windows": "Windows",
    "suse": "SUSE",
}

_S3_STORAGE_CLASS: dict[str, str] = {
    "standard": "Standard",
}

_lock = threading.Lock()
_client: Any = None
_cache: dict[str, tuple[float, Any]] = {}


class PricingUnavailable(RuntimeError):
    """La integración con la AWS Price List API no está disponible."""


def is_configured() -> bool:
    return bool(
        (settings.aws_access_key_id and settings.aws_secret_access_key)
        or settings.aws_session_token
    )


def _get_client() -> Any:
    global _client
    if _client is not None:
        return _client
    with _lock:
        if _client is not None:
            return _client
        kwargs: dict[str, Any] = {"region_name": PRICING_API_REGION}
        if settings.aws_access_key_id and settings.aws_secret_access_key:
            kwargs["aws_access_key_id"] = settings.aws_access_key_id
            kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
            if settings.aws_session_token:
                kwargs["aws_session_token"] = settings.aws_session_token
        _client = boto3.client("pricing", **kwargs)
        return _client


def _cache_get(key: str) -> Any | None:
    entry = _cache.get(key)
    if entry is None:
        return None
    expires_at, value = entry
    if expires_at <= time.monotonic():
        _cache.pop(key, None)
        return None
    return value


def _cache_set(key: str, value: Any) -> None:
    _cache[key] = (time.monotonic() + CACHE_TTL_SECONDS, value)


def _get_products(
    service_code: str,
    filters: list[dict[str, str]],
    cache_key: str,
) -> list[dict[str, Any]]:
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    if not is_configured():
        raise PricingUnavailable(
            "La integración con AWS Price List API no está configurada."
        )

    try:
        response = _get_client().get_products(
            ServiceCode=service_code,
            FormatVersion="aws_v1",
            Filters=[{"Type": "TERM_MATCH", **f} for f in filters],
            MaxResults=100,
        )
    except (BotoCoreError, ClientError) as exc:
        logger.warning("GetProducts falló para %s: %s", service_code, exc)
        raise PricingUnavailable(
            "El precio real de AWS no está disponible en este momento."
        ) from exc

    products: list[dict[str, Any]] = []
    for item in response.get("PriceList", []):
        products.append(item if isinstance(item, dict) else _loads(item))

    _cache_set(cache_key, products)
    return products


def _loads(value: Any) -> dict[str, Any]:
    import json

    if isinstance(value, str):
        return json.loads(value)
    return json.loads(str(value))


def _dimensions(product: dict[str, Any]) -> list[dict[str, Any]]:
    dimensions: list[dict[str, Any]] = []
    for offer in product.get("terms", {}).get("OnDemand", {}).values():
        dimensions.extend(offer.get("priceDimensions", {}).values())
    return dimensions


def _extract_price(
    products: list[dict[str, Any]],
    *,
    unit: str | None = None,
    tier_begin: str = "0",
) -> float | None:
    fallback: float | None = None
    for product in products:
        for dim in _dimensions(product):
            usd = dim.get("pricePerUnit", {}).get("USD")
            if usd is None:
                continue
            try:
                value = float(usd)
            except (TypeError, ValueError):
                continue
            begin = str(dim.get("beginRange", "0"))
            if unit is not None and dim.get("unit") != unit:
                if fallback is None:
                    fallback = value
                continue
            if begin == tier_begin:
                return value
            if fallback is None:
                fallback = value
    return fallback


def _first_price(products: list[dict[str, Any]], unit: str | None = None) -> float | None:
    return _extract_price(products, unit=unit)


def ec2_hourly(instance_type: str, os_key: str, location: str) -> float | None:
    os_name = _OS_MAP.get(os_key, "Linux")
    products = _get_products(
        "AmazonEC2",
        [
            {"Field": "instanceType", "Value": instance_type},
            {"Field": "location", "Value": location},
            {"Field": "operatingSystem", "Value": os_name},
            {"Field": "tenancy", "Value": "Shared"},
            {"Field": "preInstalledSw", "Value": "NA"},
            {"Field": "capacitystatus", "Value": "Used"},
        ],
        f"ec2:{location}:{instance_type}:{os_name}",
    )
    return _first_price(products, unit="Hrs")


def rds_hourly(
    instance_type: str, engine: str, multi_az: bool, location: str
) -> float | None:
    products = _get_products(
        "AmazonRDS",
        [
            {"Field": "instanceType", "Value": instance_type},
            {"Field": "location", "Value": location},
            {"Field": "databaseEngine", "Value": engine.capitalize()},
            {"Field": "deploymentOption", "Value": "Multi-AZ" if multi_az else "Single-AZ"},
        ],
        f"rds:{location}:{instance_type}:{engine}:{multi_az}",
    )
    return _first_price(products, unit="Hrs")


def rds_storage_gb(location: str, multi_az: bool) -> float | None:
    products = _get_products(
        "AmazonRDS",
        [
            {"Field": "location", "Value": location},
            {"Field": "productFamily", "Value": "Database Storage"},
            {"Field": "databaseEngine", "Value": "PostgreSQL"},
            {"Field": "volumeType", "Value": "General Purpose-GP3"},
        ],
        f"rds-storage:{location}:gp3:{multi_az}",
    )
    for product in products:
        usagetype = product.get("product", {}).get("attributes", {}).get("usagetype", "")
        if "Cluster" in usagetype:
            continue
        is_multi = "Multi-AZ" in usagetype
        if is_multi == multi_az:
            return _first_price([product], unit="GB-Mo")
    return _first_price(products, unit="GB-Mo")


def s3_gb(storage_class: str, location: str) -> float | None:
    volume_type = _S3_STORAGE_CLASS.get(storage_class)
    if volume_type is None:
        return None
    products = _get_products(
        "AmazonS3",
        [
            {"Field": "location", "Value": location},
            {"Field": "productFamily", "Value": "Storage"},
            {"Field": "volumeType", "Value": volume_type},
        ],
        f"s3:{location}:{volume_type}",
    )
    return _extract_price(products, unit="GB-Mo", tier_begin="0")


def route53_zone_month() -> float | None:
    products = _get_products(
        "AmazonRoute53",
        [{"Field": "usagetype", "Value": "HostedZone"}],
        "route53:hostedzone",
    )
    return _first_price(products, unit="HostedZone")


def route53_query_million(location: str) -> float | None:
    products = _get_products(
        "AmazonRoute53",
        [{"Field": "usagetype", "Value": "USE1-DNS-Queries"}],
        "route53:queries",
    )
    value = _extract_price(products, unit="Queries", tier_begin="0")
    if value is None:
        value = _first_price(products, unit="Queries")
    if value is None:
        return None
    return value * 1_000_000


def cloudfront_gb(region_code: str) -> float | None:
    edge = cloudfront_edge_location(region_code)
    products = _get_products(
        "AmazonCloudFront",
        [
            {"Field": "transferType", "Value": "CloudFront Outbound"},
            {"Field": "fromLocation", "Value": edge},
        ],
        f"cloudfront:{edge}",
    )
    return _extract_price(products, unit="GB", tier_begin="0")


def lambda_request_million(location: str) -> float | None:
    products = _get_products(
        "AWSLambda",
        [
            {"Field": "group", "Value": "AWS-Lambda-Requests"},
            {"Field": "location", "Value": location},
        ],
        f"lambda-request:{location}",
    )
    value = _extract_price(products, tier_begin="0")
    return None if value is None else value * 1_000_000


def lambda_gb_second(location: str) -> float | None:
    products = _get_products(
        "AWSLambda",
        [
            {"Field": "group", "Value": "AWS-Lambda-Duration"},
            {"Field": "location", "Value": location},
        ],
        f"lambda-gbsecond:{location}",
    )
    return _extract_price(products, tier_begin="0")


def verify_identity() -> dict[str, Any]:
    """Lectura garantizada de CloudTrail: identifica la cuenta IAM usada."""
    overrides: dict[str, Any] = {}
    if settings.aws_access_key_id and settings.aws_secret_access_key:
        overrides["aws_access_key_id"] = settings.aws_access_key_id
        overrides["aws_secret_access_key"] = settings.aws_secret_access_key
        if settings.aws_session_token:
            overrides["aws_session_token"] = settings.aws_session_token
    client = boto3.client("sts", region_name=PRICING_API_REGION, **overrides)
    return client.get_caller_identity()


def location_for(region_code: str, region_name: str) -> str:
    return pricing_location(region_code, region_name)
