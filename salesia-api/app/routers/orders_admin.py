from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import AuthenticatedUser, require_roles
from app.permissions import ORDERS_MANAGE, ORDERS_REVIEW, ORDERS_VIEW
from app.schemas.orders import RejectRequest
from app.schemas.orders_read import OrderDetail, OrderListResponse, OrderStatus
from app.services.orders_query import get_order_detail, list_orders
from app.services.review import (
    ReviewNotFoundError,
    ReviewStateError,
    confirm_order,
    reject_order,
    run_review,
)

router = APIRouter(prefix="/orders", tags=["orders-admin"])


@router.get(
    "",
    response_model=OrderListResponse,
    dependencies=[Depends(require_roles(*ORDERS_VIEW))],
)
def list_orders_endpoint(
    status: OrderStatus | None = Query(default=None),
    exclude_status: OrderStatus | None = Query(default=None),
    q: str | None = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> OrderListResponse:
    return list_orders(
        db,
        status=status,
        exclude_status=exclude_status,
        q=q,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{code}",
    response_model=OrderDetail,
    dependencies=[Depends(require_roles(*ORDERS_VIEW))],
)
def get_order_endpoint(
    code: Annotated[str, Path(pattern=r"^PED-\d{4,}$")],
    db: Session = Depends(get_db),
) -> OrderDetail:
    detail = get_order_detail(db, code)
    if detail is None:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return detail


@router.post("/{code}/review", response_model=OrderDetail)
def review_order_endpoint(
    code: Annotated[str, Path(pattern=r"^PED-\d{4,}$")],
    user: AuthenticatedUser = Depends(require_roles(*ORDERS_REVIEW)),
    db: Session = Depends(get_db),
) -> OrderDetail:
    return _mutate(db, code, lambda: run_review(db, code=code, actor_id=user.id))


@router.post("/{code}/confirm", response_model=OrderDetail)
def confirm_order_endpoint(
    code: Annotated[str, Path(pattern=r"^PED-\d{4,}$")],
    user: AuthenticatedUser = Depends(require_roles(*ORDERS_MANAGE)),
    db: Session = Depends(get_db),
) -> OrderDetail:
    return _mutate(
        db, code, lambda: confirm_order(db, code=code, actor_id=user.id)
    )


@router.post("/{code}/reject", response_model=OrderDetail)
def reject_order_endpoint(
    code: Annotated[str, Path(pattern=r"^PED-\d{4,}$")],
    payload: RejectRequest,
    user: AuthenticatedUser = Depends(require_roles(*ORDERS_MANAGE)),
    db: Session = Depends(get_db),
) -> OrderDetail:
    return _mutate(
        db,
        code,
        lambda: reject_order(
            db, code=code, actor_id=user.id, reason=payload.reason
        ),
    )


def _mutate(db: Session, code: str, action) -> OrderDetail:
    try:
        action()
    except ReviewNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Pedido no encontrado") from exc
    except ReviewStateError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    detail = get_order_detail(db, code)
    if detail is None:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return detail
