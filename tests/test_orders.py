from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool

from app.db import get_session
from app.main import app
from app.models import Order


@pytest.fixture()
def test_app():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    def get_test_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = get_test_session
    with TestClient(app) as test_client:
        yield test_client, engine
    app.dependency_overrides.clear()


def create_order(session: Session, **kwargs) -> Order:
    order = Order(
        customer_name=kwargs.get("customer_name", "Customer"),
        amount=kwargs.get("amount", 42.0),
        status=kwargs.get("status", "pending"),
        created_at=kwargs.get("created_at", datetime.utcnow()),
    )
    session.add(order)
    session.commit()
    session.refresh(order)
    return order


def test_create_order_success(test_app):
    client, _ = test_app
    response = client.post(
        "/orders",
        json={"customer_name": "Ada", "amount": 120.5, "status": "paid"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["customer_name"] == "Ada"
    assert data["amount"] == 120.5
    assert data["status"] == "paid"
    assert "id" in data


def test_create_order_empty_name(test_app):
    client, _ = test_app
    response = client.post(
        "/orders", json={"customer_name": "  ", "amount": 10}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "customer_name must not be empty"


def test_create_order_invalid_amount(test_app):
    client, _ = test_app
    response = client.post(
        "/orders", json={"customer_name": "Ada", "amount": 0}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "amount must be greater than 0"


def test_create_order_invalid_status(test_app):
    client, _ = test_app
    response = client.post(
        "/orders", json={"customer_name": "Ada", "amount": 10, "status": "bad"}
    )
    assert response.status_code == 400
    assert "status must be" in response.json()["detail"]


def test_list_orders_empty(test_app):
    client, _ = test_app
    response = client.get("/orders")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["pages"] == 0


def test_list_orders_pagination(test_app):
    client, engine = test_app
    with Session(engine) as session:
        for i in range(15):
            create_order(session, customer_name=f"Customer {i}", amount=10 + i)
    response = client.get("/orders", params={"page": 2, "limit": 5})
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 2
    assert data["limit"] == 5
    assert data["total"] == 15
    assert data["pages"] == 3
    assert len(data["items"]) == 5


def test_list_orders_status_filter(test_app):
    client, engine = test_app
    with Session(engine) as session:
        create_order(session, status="pending")
        create_order(session, status="paid")
    response = client.get("/orders", params={"status": "paid"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["status"] == "paid"


def test_list_orders_amount_filter(test_app):
    client, engine = test_app
    with Session(engine) as session:
        create_order(session, amount=50)
        create_order(session, amount=150)
    response = client.get("/orders", params={"min_amount": 100})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["amount"] == 150


def test_list_orders_amount_range_validation(test_app):
    client, _ = test_app
    response = client.get("/orders", params={"min_amount": 200, "max_amount": 100})
    assert response.status_code == 400
    assert response.json()["detail"] == "min_amount must be <= max_amount"


def test_list_orders_date_filter(test_app):
    client, engine = test_app
    now = datetime.utcnow()
    with Session(engine) as session:
        create_order(session, created_at=now - timedelta(days=5))
        create_order(session, created_at=now - timedelta(days=1))
    start = (now - timedelta(days=2)).isoformat()
    response = client.get("/orders", params={"start_date": start})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1


def test_list_orders_date_range_validation(test_app):
    client, _ = test_app
    response = client.get(
        "/orders",
        params={
            "start_date": "2024-01-02T00:00:00",
            "end_date": "2024-01-01T00:00:00",
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "start_date must be <= end_date"


def test_list_orders_invalid_status_filter(test_app):
    client, _ = test_app
    response = client.get("/orders", params={"status": "unknown"})
    assert response.status_code == 400


def test_list_orders_page_validation(test_app):
    client, _ = test_app
    response = client.get("/orders", params={"page": 0})
    assert response.status_code == 422


def test_list_orders_limit_validation(test_app):
    client, _ = test_app
    response = client.get("/orders", params={"limit": 101})
    assert response.status_code == 422
