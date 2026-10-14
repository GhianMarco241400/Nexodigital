from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import require_roles
from app.permissions import CUSTOMERS_VIEW
from app.schemas.customers import CustomerOut

router = APIRouter(
    prefix="/customers",
    tags=["customers"],
    dependencies=[Depends(require_roles(*CUSTOMERS_VIEW))],
)


@router.get("", response_model=list[CustomerOut])
def list_customers(db: Session = Depends(get_db)) -> list[CustomerOut]:
    rows = (
        db.execute(
            text(
                "select company_name, ruc, contact_name, email, phone, region "
                "from customers order by company_name"
            )
        )
        .mappings()
        .all()
    )
    return [CustomerOut(**row) for row in rows]
