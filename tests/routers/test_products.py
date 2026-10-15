"""Tests for /products CRUD."""

from fastapi.testclient import TestClient


def test_create_product(client: TestClient) -> None:
    response = client.post(
        "/products",
        json={"sku": "ABC", "name": "Foo", "price": 999, "stock_qty": 5},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["sku"] == "ABC"
    assert data["name"] == "Foo"
    assert data["price"] == 999
    assert data["stock_qty"] == 5


def test_create_product_duplicate_sku_returns_409(client: TestClient) -> None:
    client.post(
        "/products",
        json={"sku": "ABC", "name": "Foo", "price": 999, "stock_qty": 5},
    )
    response = client.post(
        "/products",
        json={"sku": "ABC", "name": "Dup", "price": 1, "stock_qty": 0},
    )
    assert response.status_code == 409


def test_list_products(client: TestClient) -> None:
    client.post(
        "/products",
        json={"sku": "A", "name": "A", "price": 1, "stock_qty": 0},
    )
    client.post(
        "/products",
        json={"sku": "B", "name": "B", "price": 2, "stock_qty": 0},
    )
    response = client.get("/products")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert {p["sku"] for p in data} == {"A", "B"}


def test_get_product_not_found(client: TestClient) -> None:
    response = client.get("/products/MISSING")
    assert response.status_code == 404


def test_update_product(client: TestClient) -> None:
    client.post(
        "/products",
        json={"sku": "ABC", "name": "Old", "price": 1, "stock_qty": 0},
    )
    response = client.put("/products/ABC", json={"name": "New", "price": 5})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New"
    assert data["price"] == 5
    # untouched
    assert data["stock_qty"] == 0


def test_update_product_not_found(client: TestClient) -> None:
    response = client.put("/products/MISSING", json={"name": "X"})
    assert response.status_code == 404


def test_delete_product(client: TestClient) -> None:
    client.post(
        "/products",
        json={"sku": "ABC", "name": "Foo", "price": 1, "stock_qty": 0},
    )
    response = client.delete("/products/ABC")
    assert response.status_code == 204
    assert client.get("/products/ABC").status_code == 404
