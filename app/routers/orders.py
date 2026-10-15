"""HTTP routes for /orders."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_session
from app.schemas.order import OrderCreate, OrderRead
from app.services import orders as service

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def create_order(
    data: OrderCreate,
    session: Session = Depends(get_session),
) -> OrderRead:
    """Create an order. Reserves stock atomically. Returns 404 if any SKU
    is missing; 409 if any line has insufficient stock."""
    try:
        order = service.create_order(session, data)
    except service.InsufficientStockError as exc:
        raise HTTPException(
            status_code=409, detail=f"insufficient stock for sku '{exc.sku}'"
        ) from exc
    except service.ProductNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"sku '{exc.sku}' not found") from exc
    return OrderRead.model_validate(order)


@router.get("/{order_id}", response_model=OrderRead)
def get_order(order_id: int, session: Session = Depends(get_session)) -> OrderRead:
    """Fetch an order by id. Returns 404 if missing."""
    order = service.get_order(session, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail=f"order {order_id} not found")
    return OrderRead.model_validate(order)


@router.post("/{order_id}/confirm", response_model=OrderRead)
def confirm_order(order_id: int, session: Session = Depends(get_session)) -> OrderRead:
    """Confirm a pending order. Reserves the stock without releasing it."""
    try:
        order = service.confirm_order(session, order_id)
    except service.OrderNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"order {order_id} not found") from exc
    except service.InvalidStatusTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return OrderRead.model_validate(order)


@router.post("/{order_id}/cancel", response_model=OrderRead)
def cancel_order(order_id: int, session: Session = Depends(get_session)) -> OrderRead:
    """Cancel an order from PENDING or CONFIRMED. Releases reserved stock."""
    try:
        order = service.cancel_order(session, order_id)
    except service.OrderNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"order {order_id} not found") from exc
    except service.InvalidStatusTransition as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return OrderRead.model_validate(order)
