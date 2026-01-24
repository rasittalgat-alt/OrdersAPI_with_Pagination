"""FastAPI application exposing order creation and search endpoints.

This module contains request validation, filtering logic, and pagination
helpers for the Orders Management API.
"""

from datetime import datetime
from math import ceil
from typing import Iterable, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlmodel import Session, SQLModel, func, select

from app.db import get_session, init_db
from app.models import ALLOWED_STATUSES, Order, OrderCreate, OrderRead

app = FastAPI(title="Orders Management API")

DEFAULT_STATUS = "pending"
DEFAULT_LIMIT = 10
MAX_LIMIT = 100


class OrderListResponse(SQLModel):
    """Response envelope for paginated order results."""

    items: List[OrderRead]
    page: int
    limit: int
    total: int
    pages: int


class OrderFilters(SQLModel):
    """Query-string filters applied to orders listings."""

    status: Optional[str] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


def normalize_customer_name(name: Optional[str]) -> str:
    """Return a trimmed customer name.

    The API treats whitespace-only values as invalid, so we trim input
    and leave validation to a dedicated helper.
    """

    return (name or "").strip()


def validate_customer_name(name: str) -> None:
    """Ensure the customer name is present."""

    if not name:
        raise HTTPException(status_code=400, detail="customer_name must not be empty")


def validate_amount(amount: float) -> None:
    """Ensure the order amount is a positive number."""

    if amount <= 0:
        raise HTTPException(status_code=400, detail="amount must be greater than 0")


def validate_status(value: str) -> None:
    """Ensure the order status is one of the supported values."""

    if value not in ALLOWED_STATUSES:
        raise HTTPException(
            status_code=400,
            detail="status must be pending, paid, shipped, or cancelled",
        )


def resolve_status(value: Optional[str]) -> str:
    """Return the provided status or the default status."""

    status_value = value or DEFAULT_STATUS
    validate_status(status_value)
    return status_value


def validate_amount_range(min_amount: Optional[float], max_amount: Optional[float]) -> None:
    """Ensure the amount range is not inverted."""

    if min_amount is not None and max_amount is not None and min_amount > max_amount:
        raise HTTPException(status_code=400, detail="min_amount must be <= max_amount")


def validate_date_range(
    start_date: Optional[datetime], end_date: Optional[datetime]
) -> None:
    """Ensure the date range is not inverted."""

    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be <= end_date")


def build_filters(filters: OrderFilters) -> List:
    """Translate filter inputs into SQLModel conditions."""

    clauses = []
    if filters.status:
        clauses.append(Order.status == filters.status)
    if filters.min_amount is not None:
        clauses.append(Order.amount >= filters.min_amount)
    if filters.max_amount is not None:
        clauses.append(Order.amount <= filters.max_amount)
    if filters.start_date:
        clauses.append(Order.created_at >= filters.start_date)
    if filters.end_date:
        clauses.append(Order.created_at <= filters.end_date)
    return clauses


def apply_filters(query, conditions: Iterable) -> SQLModel:
    """Apply SQLModel filter conditions to a query."""

    for condition in conditions:
        query = query.where(condition)
    return query


def calculate_pages(total: int, limit: int) -> int:
    """Calculate total number of pages for a given total and limit."""

    return ceil(total / limit) if total else 0


def paginate(
    session: Session,
    query,
    count_query,
    page: int,
    limit: int,
) -> OrderListResponse:
    """Execute a paginated query and wrap results in a response model."""

    total = session.exec(count_query).one()
    pages = calculate_pages(total, limit)
    offset = (page - 1) * limit
    items = session.exec(
        query.order_by(Order.id).offset(offset).limit(limit)
    ).all()
    return OrderListResponse(
        items=[OrderRead.from_orm(order) for order in items],
        page=page,
        limit=limit,
        total=total,
        pages=pages,
    )


@app.on_event("startup")
def on_startup() -> None:
    """Initialize database tables on startup."""

    init_db()


@app.post("/orders", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def create_order(
    payload: OrderCreate, session: Session = Depends(get_session)
) -> OrderRead:
    """Create a new order after validating required fields."""

    customer_name = normalize_customer_name(payload.customer_name)
    validate_customer_name(customer_name)
    validate_amount(payload.amount)
    status_value = resolve_status(payload.status)
    order = Order(
        customer_name=customer_name,
        amount=payload.amount,
        status=status_value,
    )
    session.add(order)
    session.commit()
    session.refresh(order)
    return OrderRead.from_orm(order)


@app.get("/orders", response_model=OrderListResponse)
def list_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    status_value: Optional[str] = Query(None, alias="status"),
    min_amount: Optional[float] = Query(None, ge=0),
    max_amount: Optional[float] = Query(None, ge=0),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    session: Session = Depends(get_session),
) -> OrderListResponse:
    """List orders with pagination and optional filtering."""

    filters = OrderFilters(
        status=status_value,
        min_amount=min_amount,
        max_amount=max_amount,
        start_date=start_date,
        end_date=end_date,
    )

    if filters.status:
        validate_status(filters.status)
    validate_amount_range(filters.min_amount, filters.max_amount)
    validate_date_range(filters.start_date, filters.end_date)

    conditions = build_filters(filters)
    query = apply_filters(select(Order), conditions)
    count_query = apply_filters(select(func.count()).select_from(Order), conditions)

    return paginate(session, query, count_query, page, limit)
