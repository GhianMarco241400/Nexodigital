"""Utilidades de región para la AWS Price List API.

La Price List API filtra por `location`, un nombre que NO siempre coincide con
el nombre de visualización de `aws_regions.name` (p. ej. el display es
"Europe (Ireland)" pero el filtro real es "EU (Ireland)"). Además solo acepta
caracteres ASCII, así que se normalizan los acentos.
"""

import unicodedata

PRICING_LOCATION_OVERRIDES: dict[str, str] = {
    "eu-west-1": "EU (Ireland)",
    "eu-west-2": "EU (London)",
    "eu-west-3": "EU (Paris)",
    "eu-central-1": "EU (Frankfurt)",
    "eu-north-1": "EU (Stockholm)",
    "eu-south-1": "EU (Milan)",
}


def ascii_location(name: str) -> str:
    decomposed = unicodedata.normalize("NFD", name)
    without_diacritics = "".join(
        ch for ch in decomposed if unicodedata.category(ch) != "Mn"
    )
    cleaned = "".join(
        ch
        if ch.isalnum() or ch in " ()%&+-.,/:;<=>_"
        else "-"
        for ch in without_diacritics
    )
    return " ".join(cleaned.split()).strip()


def pricing_location(region_code: str, region_name: str) -> str:
    raw = PRICING_LOCATION_OVERRIDES.get(region_code, region_name)
    return ascii_location(raw)


_CLOUDFRONT_EDGE_GROUPS: tuple[tuple[str, str], ...] = (
    ("us-", "United States"),
    ("ca-", "Canada"),
    ("eu-", "Europe"),
    ("ap-", "Asia Pacific"),
    ("sa-", "South America"),
    ("me-", "Middle East"),
    ("af-", "Africa"),
    ("il-", "Israel"),
)


def cloudfront_edge_location(region_code: str) -> str:
    for prefix, location in _CLOUDFRONT_EDGE_GROUPS:
        if region_code.startswith(prefix):
            return location
    return "United States"
