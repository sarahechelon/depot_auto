"""Tests for /orders endpoints and stock-reservation semantics."""

from fastapi.testclient import TestClient


def _create_product(
    client: TestClient,
    sku: str = "ABC",
    stock: int = 10,
    price: int = 100,
) -> dict:
    response = client.post(
        "/products",
        json={"sku": sku, "name": "Foo", "price": price, "stock_qty": stock},
    )
    assert response.status_code == 201
    return response.json()


def test_create_order(client: TestClient) -> None:
    _create_product(client, stock=10)
    response = client.post(
        "/orders",
        json={"customer_email": "a@b.com", "lines": [{"sku": "ABC", "quantity": 3}]},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    assert len(data["lines"]) == 1
    assert data["lines"][0]["sku"] == "ABC"
    assert data["lines"][0]["quantity"] == 3
    assert data["lines"][0]["unit_price_cents"] == 100


def test_create_order_decrements_stock(client: TestClient) -> None:
    _create_product(client, stock=10)
    client.post(
        "/orders",
        json={"customer_email": "a@b.com", "lines": [{"sku": "ABC", "quantity": 3}]},
    )
    response = client.get("/products/ABC")
    assert response.json()["stock_qty"] == 7


def test_create_order_unknown_sku_returns_404(client: TestClient) -> None:
    response = client.post(
        "/orders",
        json={"customer_email": "a@b.com", "lines": [{"sku": "NOPE", "quantity": 1}]},
    )
    assert response.status_code == 404


def test_create_order_insufficient_stock_returns_409(client: TestClient) -> None:
    _create_product(client, stock=2)
    response = client.post(
        "/orders",
        json={"customer_email": "a@b.com", "lines": [{"sku": "ABC", "quantity": 5}]},
    )
    assert response.status_code == 409


def test_create_order_insufficient_stock_no_partial_decrement(
    client: TestClient,
) -> None:
    """A failure on a later SKU must not leak decrements from earlier ones."""
    _create_product(client, stock=2)
    client.post(
        "/orders",
        json={
            "customer_email": "a@b.com",
            "lines": [{"sku": "ABC", "quantity": 1}, {"sku": "ABC", "quantity": 5}],
        },
    )
    response = client.get("/products/ABC")
    assert response.json()["stock_qty"] == 2


def test_confirm_order(client: TestClient) -> None:
    _create_product(client, stock=10)
    order_id = client.post(
        "/orders",
        json={"customer_email": "a@b.com", "lines": [{"sku": "ABC", "quantity": 3}]},
    ).json()["id"]
    response = client.post(f"/orders/{order_id}/confirm")
    assert response.status_code == 200
    assert response.json()["status"] == "confirmed"
    # confirm does not release stock
    assert client.get("/products/ABC").json()["stock_qty"] == 7


def test_confirm_unknown_order_returns_404(client: TestClient) -> None:
    response = client.post("/orders/9999/confirm")
    assert response.status_code == 404


def test_confirm_already_confirmed_returns_409(client: TestClient) -> None:
    _create_product(client, stock=10)
    order_id = client.post(
        "/orders",
        json={"customer_email": "a@b.com", "lines": [{"sku": "ABC", "quantity": 1}]},
    ).json()["id"]
    client.post(f"/orders/{order_id}/confirm")
    response = client.post(f"/orders/{order_id}/confirm")
    assert response.status_code == 409


def test_cancel_pending_restores_stock(client: TestClient) -> None:
    _create_product(client, stock=10)
    order_id = client.post(
        "/orders",
        json={"customer_email": "a@b.com", "lines": [{"sku": "ABC", "quantity": 3}]},
    ).json()["id"]
    response = client.post(f"/orders/{order_id}/cancel")
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    assert client.get("/products/ABC").json()["stock_qty"] == 10


def test_cancel_confirmed_restores_stock(client: TestClient) -> None:
    _create_product(client, stock=10)
    order_id = client.post(
        "/orders",
        json={"customer_email": "a@b.com", "lines": [{"sku": "ABC", "quantity": 3}]},
    ).json()["id"]
    client.post(f"/orders/{order_id}/confirm")
    client.post(f"/orders/{order_id}/cancel")
    assert client.get("/products/ABC").json()["stock_qty"] == 10


def test_already_cancelled_returns_409(client: TestClient) -> None:
    _create_product(client, stock=10)
    order_id = client.post(
        "/orders",
        json={"customer_email": "a@b.com", "lines": [{"sku": "ABC", "quantity": 1}]},
    ).json()["id"]
    client.post(f"/orders/{order_id}/cancel")
    response = client.post(f"/orders/{order_id}/cancel")
    assert response.status_code == 409
