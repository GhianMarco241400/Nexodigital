from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel

OrderStatus = Literal["pendiente", "en_revision", "confirmado", "rechazado"]


class OrderListItem(BaseModel):
    code: str
    company_name: str
    plan_name: str
    monthly_total: float
    setup_total: float
    status: str
    risk: str
    created_at: datetime


class OrderCounts(BaseModel):
    total: int
    pendiente: int
    en_revision: int
    confirmado: int
    rechazado: int
    ingresos_confirmado: float = 0


class OrderListResponse(BaseModel):
    items: list[OrderListItem]
    total: int
    page: int
    page_size: int
    counts: OrderCounts


class CustomerInfo(BaseModel):
    company_name: str
    ruc: str
    contact_name: str
    email: str
    phone: str | None = None
    region: str | None = None


class PlanInfo(BaseModel):
    code: str
    name: str
    description: str | None = None
    monthly_price: float
    setup_price: float


class OrderItemInfo(BaseModel):
    extra_name: str
    monthly_price: float
    setup_price: float
    quantity: int


class ComponentLine(BaseModel):
    label: str
    amount: float


class InfraComponentInfo(BaseModel):
    service_code: str
    usd_monthly: float
    breakdown: list[ComponentLine] = []


class StaffRef(BaseModel):
    id: int
    full_name: str


class ReviewInfo(BaseModel):
    summary: str
    flags: Any | None = None
    risk: str
    recommendation: str | None = None
    confidence: float | None = None
    model: str | None = None
    created_at: datetime


class OrderEventInfo(BaseModel):
    event_type: str
    description: str | None = None
    actor_name: str | None = None
    created_at: datetime


class OrderDetail(BaseModel):
    code: str
    status: str
    risk: str
    region_code: str
    created_at: datetime
    monthly_total: float
    setup_total: float
    infra_usd: float = 0
    infra_estimate: float = 0
    fx_rate: float = 0
    customer: CustomerInfo
    plan: PlanInfo
    items: list[OrderItemInfo]
    infra_components: list[InfraComponentInfo] = []
    assigned_to: StaffRef | None = None
    reviewed_by: StaffRef | None = None
    reviewed_at: datetime | None = None
    reject_reason: str | None = None
    review: ReviewInfo | None = None
    events: list[OrderEventInfo]
