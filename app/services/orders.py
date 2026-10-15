"""Business logic for orders, including atomic stock reservation."""

from collections.abc import Iterable, Mapping

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.order import Order, OrderLine, OrderStatus
from app.models.product import Product
from app.schemas.order import OrderCreate


class InsufficientStockError(Exception):
    """Raised when an order lines cannot be reserved against current stock."""

    def __init__(self, sku: str) -> None:
        super().__init__(sku)
        self.sku = sku


class ProductNotFoundError(Exception):
    """Raised when a referenced SKU does not exist."""

    def __init__(self, sku: str) -> None:
        super().__init__(sku)
        self.sku = sku


class OrderNotFoundError(Exception):
    """Raised when an order id does not exist."""

    def __init__(self, order_id: int) -> None:
        super().__init__(order_id)
        self.order_id = order_id


class InvalidStatusTransition(Exception):
    """Raised when an order is asked to transition from an invalid state."""


def _aggregate_quantities(items: Iterable[tuple[str, int]]) -> Mapping[str, int]:
    out: dict[str, int] = {}
    for sku, qty in items:
        out[sku] = out.get(sku, 0) + qty
    return out


def get_order(session: Session, order_id: int) -> Order | None:
    """Return an order by id, or None if missing."""
    return session.get(Order, order_id)


def create_order(session: Session, data: OrderCreate) -> Order:
    """Create an order and atomically reserve stock for each SKU.

    Validates that all line SKUs exist (raises ProductNotFoundError if not).
    Aggregates quantities by SKU and runs an atomic SQL UPDATE per SKU; the
    guard is `stock_qty >= qty`. If the row is updated by zero rows, the
    service raises InsufficientStockError and the transaction is rolled
    back so no partial decrements happen. On success the order is persisted
    with snapshotted unit prices (taken at request time).
    """
    skus = list({line.sku for line in data.lines})
    products = session.scalars(select(Product).where(Product.sku.in_(skus))).all()
    db_products = {p.sku: p for p in products}
    for line in data.lines:
        if line.sku not in db_products:
            raise ProductNotFoundError(line.sku)

    quantities = _aggregate_quantities((line.sku, line.quantity) for line in data.lines)

    try:
        for sku, qty in quantities.items():
            result = session.execute(
                update(Product)
                .where(Product.sku == sku, Product.stock_qty >= qty)
                .values(stock_qty=Product.stock_qty - qty)
            )
            if result.rowcount != 1:
                raise InsufficientStockError(sku)
        order = Order(
            customer_email=data.customer_email,
            status=OrderStatus.PENDING,
        )
        for line in data.lines:
            order.lines.append(
                OrderLine(
                    sku=line.sku,
                    quantity=line.quantity,
                    unit_price_cents=db_products[line.sku].price,
                )
            )
        session.add(order)
        session.commit()
    except (InsufficientStockError, ProductNotFoundError):
        session.rollback()
        raise

    session.refresh(order)
    return order


def confirm_order(session: Session, order_id: int) -> Order:
    """Transition a pending order to confirmed. Stock stays reserved."""
    order = session.get(Order, order_id)
    if order is None:
        raise OrderNotFoundError(order_id)
    if order.status != OrderStatus.PENDING:
        raise InvalidStatusTransition(f"cannot confirm order in status {order.status.value}")
    order.status = OrderStatus.CONFIRMED
    session.commit()
    session.refresh(order)
    return order


def cancel_order(session: Session, order_id: int) -> Order:
    """Cancel a non-cancelled order and restore stock for each line.

    Works from either PENDING or CONFIRMED: in both cases the reservation
    is held by the order lines, so we can atomically credit each SKU back
    via UPDATE ... SET stock_qty = stock_qty + :qty.
    """
    order = session.get(Order, order_id)
    if order is None:
        raise OrderNotFoundError(order_id)
    if order.status == OrderStatus.CANCELLED:
        raise InvalidStatusTransition("order is already cancelled")

    quantities = _aggregate_quantities((line.sku, line.quantity) for line in order.lines)
    try:
        for sku, qty in quantities.items():
            session.execute(
                update(Product).where(Product.sku == sku).values(stock_qty=Product.stock_qty + qty)
            )
        order.status = OrderStatus.CANCELLED
        session.commit()
    except Exception:
        session.rollback()
        raise

    session.refresh(order)
    return order
