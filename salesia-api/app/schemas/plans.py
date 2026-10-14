from pydantic import BaseModel


class PlanOut(BaseModel):
    code: str
    name: str
    description: str | None = None
    monthly_price: float
    setup_price: float
