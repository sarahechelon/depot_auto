"""Business logic for products. Never imports FastAPI."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


class DuplicateSkuError(Exception):
    """Raised when a product SKU already exists."""


class NotFoundError(Exception):
    """Raised when a product does not exist."""


class InUseError(Exception):
    """Raised when a product cannot be deleted because something references it."""

    def __init__(self, sku: str) -> None:
        super().__init__(sku)
        self.sku = sku


def get_product(session: Session, sku: str) -> Product | None:
    """Return a product by SKU, or None if missing."""
    return session.get(Product, sku)


def list_products(session: Session) -> list[Product]:
    """Return all products."""
    return list(session.scalars(select(Product)).all())


def create_product(session: Session, data: ProductCreate) -> Product:
    """Create a new product. Raises DuplicateSkuError on PK conflict."""
    product = Product(
        sku=data.sku,
        name=data.name,
        price=data.price,
        stock_qty=data.stock_qty,
    )
    session.add(product)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise DuplicateSkuError(data.sku) from exc
    session.refresh(product)
    return product


def update_product(session: Session, sku: str, data: ProductUpdate) -> Product:
    """Update an existing product. Raises NotFoundError if missing."""
    product = session.get(Product, sku)
    if product is None:
        raise NotFoundError(sku)
    if data.name is not None:
        product.name = data.name
    if data.price is not None:
        product.price = data.price
    if data.stock_qty is not None:
        product.stock_qty = data.stock_qty
    session.commit()
    session.refresh(product)
    return product


def delete_product(session: Session, sku: str) -> None:
    """Delete a product. Raises NotFoundError if missing; InUseError if any
    order_line references the sku (FK violation)."""
    product = session.get(Product, sku)
    if product is None:
        raise NotFoundError(sku)
    session.delete(product)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise InUseError(sku) from exc
