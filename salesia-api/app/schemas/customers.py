from pydantic import BaseModel


class CustomerOut(BaseModel):
    company_name: str
    ruc: str
    contact_name: str
    email: str
    phone: str | None = None
    region: str | None = None
