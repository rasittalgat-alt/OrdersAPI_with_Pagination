"""Seed script for inserting sample orders into the database."""

import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable, List

from sqlmodel import Session, select

from app.db import engine, init_db
from app.models import ALLOWED_STATUSES, Order

DEFAULT_ORDER_COUNT = 50
MIN_AMOUNT = 10
MAX_AMOUNT = 500


@dataclass(frozen=True)
class SeedConfig:
    """Configuration for generating sample order data."""

    count: int = DEFAULT_ORDER_COUNT
    min_amount: int = MIN_AMOUNT
    max_amount: int = MAX_AMOUNT


def database_has_orders(session: Session) -> bool:
    """Return True when at least one order exists."""

    return session.exec(select(Order)).first() is not None


def build_seed_orders(config: SeedConfig) -> List[Order]:
    """Create a list of Order objects using the seed configuration."""

    base_time = datetime.utcnow() - timedelta(days=config.count)
    statuses = sorted(ALLOWED_STATUSES)
    orders: List[Order] = []
    for index in range(1, config.count + 1):
        orders.append(
            Order(
                customer_name=f"Customer {index}",
                amount=round(random.uniform(config.min_amount, config.max_amount), 2),
                status=random.choice(statuses),
                created_at=base_time + timedelta(days=index),
            )
        )
    return orders


def insert_orders(session: Session, orders: Iterable[Order]) -> int:
    """Persist seed orders to the database and return the count."""

    order_list = list(orders)
    if not order_list:
        return 0
    session.add_all(order_list)
    session.commit()
    return len(order_list)


def format_summary(inserted: int) -> str:
    """Return a human-friendly summary string."""

    return f"Inserted {inserted} orders"


def seed_orders(config: SeedConfig | None = None) -> int:
    """Seed the database with sample orders if empty.

    Returns the number of orders inserted (0 if already populated).
    """

    init_db()
    config = config or SeedConfig()
    with Session(engine) as session:
        if database_has_orders(session):
            return 0
        orders = build_seed_orders(config)
        return insert_orders(session, orders)


if __name__ == "__main__":
    inserted = seed_orders()
    print(format_summary(inserted))
