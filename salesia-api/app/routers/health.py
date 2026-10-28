import traceback
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import engine, get_db
from app.init_db import init_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health(db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        db.execute(text("select 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "ok", "database": "disconnected", "error": str(e)[:200]}


@router.get("/health/db-init")
def health_db_init() -> dict:
    try:
        init_db(engine)
        return {"status": "ok", "message": "Base de datos inicializada correctamente"}
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc(),
        }
