"""Concurrency: 20 parallel orders against stock=10 must never oversell."""

import threading

from sqlalchemy import func as sa_func
from sqlalchemy import select

from app.models.order import Order, OrderLine, OrderStatus
from app.models.product import Product
from app.schemas.order import OrderCreate, OrderLineCreate
from app.services.orders import InsufficientStockError, create_order


def test_twenty_parallel_orders_dont_oversell(session_factory) -> None:
    """Seed stock=10, fire 20 concurrent single-unit orders, expect 10
    successes and 10 InsufficientStockError failures; final stock_qty == 0
    and total reserved across (pending|confirmed) orders == 10."""
    with session_factory() as s:
        s.add(Product(sku="ABC", name="Foo", price=100, stock_qty=10))
        s.commit()

    barrier = threading.Barrier(20)
    successes: list[int] = []
    failures: list[int] = []
    s_lock = threading.Lock()
    f_lock = threading.Lock()

    def worker(idx: int) -> None:
        barrier.wait()
        try:
            with session_factory() as s:
                data = OrderCreate(
                    customer_email=f"u{idx}@b.com",
                    lines=[OrderLineCreate(sku="ABC", quantity=1)],
                )
                create_order(s, data)
            with s_lock:
                successes.append(idx)
        except InsufficientStockError:
            with f_lock:
                failures.append(idx)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(successes) == 10, f"expected 10 successes, got {len(successes)}"
    assert len(failures) == 10, f"expected 10 failures, got {len(failures)}"

    with session_factory() as s:
        product = s.scalar(select(Product).where(Product.sku == "ABC"))
        assert product is not None
        assert product.stock_qty == 0

        # Sum of reserved quantities across non-cancelled orders must equal
        # the initial stock. If anything > 10 sneaked through, we'd see > 10
        # here (we'd have oversold).
        reserved_total = (
            s.scalar(
                select(sa_func.coalesce(sa_func.sum(OrderLine.quantity), 0))
                .join(Order, OrderLine.order_id == Order.id)
                .where(Order.status != OrderStatus.CANCELLED)
            )
            or 0
        )
        assert reserved_total == 10
