"""Pydantic schemas for /products endpoints."""

from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    sku: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=200)
    price: int = Field(..., ge=0)
    stock_qty: int = Field(0, ge=0)


class ProductUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    price: int | None = Field(None, ge=0)
    stock_qty: int | None = Field(None, ge=0)


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sku: str
    name: str
    price: int
    stock_qty: int
