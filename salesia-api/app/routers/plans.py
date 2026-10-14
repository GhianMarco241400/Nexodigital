from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.plans import PlanOut

router = APIRouter(tags=["plans"])


@router.get("/plans", response_model=list[PlanOut])
def list_plans(db: Session = Depends(get_db)) -> list[PlanOut]:
    rows = (
        db.execute(
            text(
                "select code, name, description, monthly_price, setup_price "
                "from plans where active = true order by monthly_price"
            )
        )
        .mappings()
        .all()
    )
    return [PlanOut(**row) for row in rows]
