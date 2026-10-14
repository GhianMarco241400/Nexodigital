from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import AuthenticatedUser, require_roles
from app.permissions import SETTINGS_ADMIN
from app.schemas.review_config import (
    ReviewConfigOut,
    ReviewConfigUpdate,
    ReviewTestResult,
)
from app.services.review_config import get_review_config, set_review_config, test_provider

router = APIRouter(
    prefix="/settings",
    tags=["settings"],
    dependencies=[Depends(require_roles(*SETTINGS_ADMIN))],
)


@router.get("/review", response_model=ReviewConfigOut)
def get_review_settings(db: Session = Depends(get_db)) -> ReviewConfigOut:
    return get_review_config(db)


@router.put("/review", response_model=ReviewConfigOut)
def update_review_settings(
    payload: ReviewConfigUpdate,
    user: AuthenticatedUser = Depends(require_roles(*SETTINGS_ADMIN)),
    db: Session = Depends(get_db),
) -> ReviewConfigOut:
    set_review_config(
        db,
        mode=payload.mode,
        provider=payload.provider,
        model=payload.model,
        actor_id=user.id,
    )
    return get_review_config(db)


@router.post("/review/test", response_model=ReviewTestResult)
def test_review_endpoint(db: Session = Depends(get_db)) -> ReviewTestResult:
    return test_provider(db)
