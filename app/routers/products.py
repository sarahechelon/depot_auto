"""HTTP routes for /products."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_session
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate
from app.services import products as service

router = APIRouter(prefix="/products", tags=["products"])


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(data: ProductCreate, session: Session = Depends(get_session)) -> ProductRead:
    """Create a product. Returns 409 if SKU already exists."""
    try:
        product = service.create_product(session, data)
    except service.DuplicateSkuError as exc:
        raise HTTPException(status_code=409, detail=f"sku '{data.sku}' already exists") from exc
    return ProductRead.model_validate(product)


@router.get("", response_model=list[ProductRead])
def list_products(session: Session = Depends(get_session)) -> list[ProductRead]:
    """List all products."""
    products = service.list_products(session)
    return [ProductRead.model_validate(p) for p in products]


@router.get("/{sku}", response_model=ProductRead)
def get_product(sku: str, session: Session = Depends(get_session)) -> ProductRead:
    """Fetch a single product by SKU. Returns 404 if missing."""
    product = service.get_product(session, sku)
    if product is None:
        raise HTTPException(status_code=404, detail=f"sku '{sku}' not found")
    return ProductRead.model_validate(product)


@router.put("/{sku}", response_model=ProductRead)
def update_product(
    sku: str,
    data: ProductUpdate,
    session: Session = Depends(get_session),
) -> ProductRead:
    """Update a product. Returns 404 if missing."""
    try:
        product = service.update_product(session, sku, data)
    except service.NotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"sku '{sku}' not found") from exc
    return ProductRead.model_validate(product)


@router.delete("/{sku}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(sku: str, session: Session = Depends(get_session)) -> None:
    """Delete a product. Returns 404 if missing; 409 if referenced by orders."""
    try:
        service.delete_product(session, sku)
    except service.NotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"sku '{sku}' not found") from exc
    except service.InUseError as exc:
        raise HTTPException(status_code=409, detail=f"sku '{sku}' is referenced by orders") from exc
