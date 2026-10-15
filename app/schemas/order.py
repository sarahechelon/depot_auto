"""Pydantic schemas for /orders endpoints."""

from pydantic import BaseModel, ConfigDict, Field

from app.models.order import OrderStatus


class OrderLineCreate(BaseModel):
    """A request-side line: sku + quantity. Server snapshots price at create."""

    sku: str = Field(..., min_length=1, max_length=64)
    quantity: int = Field(..., ge=1)


class OrderCreate(BaseModel):
    customer_email: str = Field(..., min_length=3, max_length=200)
    lines: list[OrderLineCreate] = Field(..., min_length=1)


class OrderLineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sku: str
    quantity: int
    unit_price_cents: int


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_email: str
    status: OrderStatus
    lines: list[OrderLineRead]
