from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.orders import OrderCreate, OrderCreated
from app.services.orders import OrderBusinessError, create_order

router = APIRouter(tags=["orders"])


@router.post("/orders", status_code=201, response_model=OrderCreated)
def create_order_endpoint(
    payload: OrderCreate,
    db: Session = Depends(get_db),
) -> OrderCreated:
    # TODO: endpoint público de la landing. Agregar rate limiting y captcha,
    # y autenticación cuando se implemente.
    try:
        return create_order(db, payload)
    except OrderBusinessError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
