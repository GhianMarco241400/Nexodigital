from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health(db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        db.execute(text("select 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "ok", "database": "disconnected", "error": str(e)[:200]}
