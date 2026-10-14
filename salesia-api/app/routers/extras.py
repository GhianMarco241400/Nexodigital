from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.extras import ExtraOut

router = APIRouter(tags=["extras"])


@router.get("/extras", response_model=list[ExtraOut])
def list_extras(db: Session = Depends(get_db)) -> list[ExtraOut]:
    rows = (
        db.execute(
            text(
                "select code, name, description, monthly_price, setup_price "
                "from extras where active = true order by monthly_price, name"
            )
        )
        .mappings()
        .all()
    )
    return [ExtraOut(**row) for row in rows]
