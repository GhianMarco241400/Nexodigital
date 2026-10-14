from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, StringConstraints, field_validator

CompanyName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=2, max_length=200)
]
Ruc = Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^\d{11}$")]
PlanCode = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)
]
Phone = Annotated[str, StringConstraints(strip_whitespace=True, max_length=20)]
Region = Annotated[str, StringConstraints(strip_whitespace=True, max_length=100)]
AwsRegion = Annotated[
    str, StringConstraints(strip_whitespace=True, pattern=r"^[a-z]{2}-[a-z]+-\d$", max_length=20)
]


class OrderCreate(BaseModel):
    company_name: CompanyName
    ruc: Ruc
    contact_name: CompanyName
    email: EmailStr
    phone: Phone | None = None
    region: Region | None = None
    plan_code: PlanCode
    extra_codes: list[PlanCode] = Field(default_factory=list, max_length=10)
    region_code: AwsRegion | None = None

    @field_validator("extra_codes", mode="before")
    @classmethod
    def normalize_extra_codes(cls, value: object) -> object:
        if not isinstance(value, list):
            return value
        seen: set[str] = set()
        result: list[str] = []
        for item in value:
            if not isinstance(item, str):
                return value
            code = item.strip()
            if not code or code in seen:
                continue
            seen.add(code)
            result.append(code)
        return result


class PlanSummary(BaseModel):
    code: str
    name: str


class ExtraSummary(BaseModel):
    code: str
    name: str


class OrderCreated(BaseModel):
    code: str
    status: str
    plan: PlanSummary
    extras: list[ExtraSummary]
    monthly_total: float
    setup_total: float


class RejectRequest(BaseModel):
    reason: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=3, max_length=300)
    ]
