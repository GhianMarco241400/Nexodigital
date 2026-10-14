from typing import Any, Literal

from pydantic import BaseModel, Field

QuoteSource = Literal["live", "stored"]


class CatalogMeta(BaseModel):
    provider: str = "AWS"
    mode: str
    notice: str
    reference_date: str
    currency: str = "USD"
    igv: float
    service_count: int
    region_count: int
    fx_rates: dict[str, float]


class RegionOut(BaseModel):
    code: str
    name: str
    city: str | None = None
    country: str | None = None
    lat: float | None = None
    lng: float | None = None
    price_factor: float


class ServiceOut(BaseModel):
    code: str
    name: str
    category: str
    description: str | None = None


class QuoteLine(BaseModel):
    label: str
    amount: float


class ComponentQuote(BaseModel):
    service_code: str
    name: str
    source: QuoteSource
    monthly_usd: float
    breakdown: list[QuoteLine]


class QuoteRequest(BaseModel):
    region_code: str = "us-east-1"
    plan_code: str | None = None
    services: list["ServiceSpec"] | None = None


class ServiceSpec(BaseModel):
    service_code: str
    params: dict[str, Any] = Field(default_factory=dict)


class QuoteResponse(BaseModel):
    region_code: str
    region_name: str
    currency: str = "USD"
    mode: str
    reference_date: str
    notice: str
    monthly_usd: float
    monthly_pen: float | None = None
    components: list[ComponentQuote]


QuoteRequest.model_rebuild()
