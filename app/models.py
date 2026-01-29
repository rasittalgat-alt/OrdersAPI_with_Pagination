from datetime import datetime
from typing import Optional

from pydantic import validator
from sqlalchemy import Index
from sqlmodel import Field, SQLModel

ALLOWED_STATUSES = {"pending", "paid", "shipped", "cancelled"}


class OrderBase(SQLModel):
    customer_name: str
    amount: float
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @validator("customer_name")
    def customer_name_not_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("customer_name must not be empty")
        return value

    @validator("amount")
    def amount_positive(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("amount must be greater than 0")
        return value

    @validator("status")
    def status_allowed(cls, value: str) -> str:
        if value not in ALLOWED_STATUSES:
            raise ValueError("status must be pending, paid, shipped, or cancelled")
        return value


class Order(OrderBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    __table_args__ = (
        Index("ix_order_status", "status"),
        Index("ix_order_amount", "amount"),
        Index("ix_order_created_at", "created_at"),
    )


class OrderCreate(SQLModel):
    customer_name: str
    amount: float
    status: Optional[str] = "pending"


class OrderRead(OrderBase):
    id: int
