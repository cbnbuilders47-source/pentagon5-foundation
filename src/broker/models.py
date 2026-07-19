from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import StrEnum


class OrderSide(StrEnum):
    BUY = "buy"
    SELL = "sell"


class OrderType(StrEnum):
    MARKET = "market"
    LIMIT = "limit"


class OrderStatus(StrEnum):
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


def _validate_positive(value: Decimal, name: str) -> None:
    if value <= Decimal("0"):
        raise ValueError(f"{name} must be positive")


def _validate_limit_order(order_type: OrderType, limit_price: Decimal | None) -> None:
    if order_type is OrderType.LIMIT and limit_price is None:
        raise ValueError("limit orders require a limit price")
    if limit_price is not None:
        _validate_positive(limit_price, "limit price")


@dataclass(frozen=True, slots=True)
class OrderRequest:
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: Decimal
    requested_at: datetime
    limit_price: Decimal | None = None

    def __post_init__(self) -> None:
        _validate_positive(self.quantity, "quantity")
        _validate_limit_order(self.order_type, self.limit_price)


@dataclass(frozen=True, slots=True)
class Order:
    id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: Decimal
    status: OrderStatus
    created_at: datetime
    updated_at: datetime
    limit_price: Decimal | None = None

    def __post_init__(self) -> None:
        _validate_positive(self.quantity, "quantity")
        _validate_limit_order(self.order_type, self.limit_price)


@dataclass(frozen=True, slots=True)
class Execution:
    id: str
    order_id: str
    symbol: str
    side: OrderSide
    quantity: Decimal
    price: Decimal
    executed_at: datetime

    def __post_init__(self) -> None:
        _validate_positive(self.quantity, "quantity")
        _validate_positive(self.price, "price")


@dataclass(frozen=True, slots=True)
class Position:
    symbol: str
    quantity: Decimal
    average_price: Decimal
    updated_at: datetime

    def __post_init__(self) -> None:
        _validate_positive(self.quantity, "quantity")
        _validate_positive(self.average_price, "average price")


@dataclass(frozen=True, slots=True)
class Account:
    id: str
    cash_balance: Decimal
    equity: Decimal
    buying_power: Decimal
    updated_at: datetime
    positions: tuple[Position, ...] = field(default_factory=tuple)
