from abc import ABC, abstractmethod
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from src.broker.models import (
    Account,
    Execution,
    Order,
    OrderRequest,
    OrderSide,
    OrderStatus,
    OrderType,
    Position,
)


class BrokerProvider(ABC):
    """Interface for broker connectivity and account operations."""

    @abstractmethod
    def connect(self) -> None:
        """Connect to the broker."""
        raise NotImplementedError

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the broker."""
        raise NotImplementedError

    @abstractmethod
    def is_connected(self) -> bool:
        """Return whether the broker connection is active."""
        raise NotImplementedError

    @abstractmethod
    def place_order(self, request: OrderRequest) -> Order:
        """Submit an order request."""
        raise NotImplementedError

    @abstractmethod
    def cancel_order(self, order_id: str) -> Order:
        """Cancel an existing order."""
        raise NotImplementedError

    @abstractmethod
    def get_order(self, order_id: str) -> Order:
        """Return an order by identifier."""
        raise NotImplementedError

    @abstractmethod
    def get_executions(self, order_id: str | None = None) -> tuple[Execution, ...]:
        """Return executions, optionally filtered by order."""
        raise NotImplementedError

    @abstractmethod
    def get_positions(self) -> tuple[Position, ...]:
        """Return current positions."""
        raise NotImplementedError

    @abstractmethod
    def get_account(self) -> Account:
        """Return the current account."""
        raise NotImplementedError


class MockBrokerProvider(BrokerProvider):
    """In-memory broker that immediately fills market orders."""

    MARKET_PRICE = Decimal("100")
    STARTING_CASH = Decimal("100000")

    def __init__(self) -> None:
        now = datetime.now(UTC)
        self._connected = False
        self._orders: dict[str, Order] = {}
        self._executions: list[Execution] = []
        self._positions: dict[str, Position] = {}
        self._account = Account(
            id=str(uuid4()),
            cash_balance=self.STARTING_CASH,
            equity=self.STARTING_CASH,
            buying_power=self.STARTING_CASH,
            updated_at=now,
        )

    def connect(self) -> None:
        """Mark the in-memory provider as connected."""
        self._connected = True

    def disconnect(self) -> None:
        """Mark the in-memory provider as disconnected."""
        self._connected = False

    def is_connected(self) -> bool:
        """Return whether the provider is connected."""
        return self._connected

    def place_order(self, request: OrderRequest) -> Order:
        """Immediately fill a market order at the fixed test price."""
        self._require_connected()
        if request.order_type is OrderType.LIMIT:
            raise NotImplementedError("MockBrokerProvider supports market orders only")

        now = datetime.now(UTC)
        order = Order(
            id=str(uuid4()),
            symbol=request.symbol,
            side=request.side,
            order_type=request.order_type,
            quantity=request.quantity,
            status=OrderStatus.FILLED,
            created_at=now,
            updated_at=now,
        )
        execution = Execution(
            id=str(uuid4()),
            order_id=order.id,
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=self.MARKET_PRICE,
            executed_at=now,
        )

        self._apply_fill(execution)
        self._orders[order.id] = order
        self._executions.append(execution)
        self._refresh_account(now)
        return order

    def cancel_order(self, order_id: str) -> Order:
        """Cancel a pending order."""
        self._require_connected()
        order = self.get_order(order_id)
        if order.status is not OrderStatus.PENDING:
            raise ValueError("only pending orders can be cancelled")

        cancelled = Order(
            id=order.id,
            symbol=order.symbol,
            side=order.side,
            order_type=order.order_type,
            quantity=order.quantity,
            status=OrderStatus.CANCELLED,
            created_at=order.created_at,
            updated_at=datetime.now(UTC),
            limit_price=order.limit_price,
        )
        self._orders[order_id] = cancelled
        return cancelled

    def get_order(self, order_id: str) -> Order:
        """Return an in-memory order by identifier."""
        self._require_connected()
        try:
            return self._orders[order_id]
        except KeyError as error:
            raise ValueError(f"unknown order: {order_id}") from error

    def get_executions(self, order_id: str | None = None) -> tuple[Execution, ...]:
        """Return all executions or those for one order."""
        self._require_connected()
        if order_id is None:
            return tuple(self._executions)
        return tuple(execution for execution in self._executions if execution.order_id == order_id)

    def get_positions(self) -> tuple[Position, ...]:
        """Return current positions sorted by symbol."""
        self._require_connected()
        return tuple(self._positions[symbol] for symbol in sorted(self._positions))

    def get_account(self) -> Account:
        """Return the current in-memory account snapshot."""
        self._require_connected()
        return self._account

    def _require_connected(self) -> None:
        if not self._connected:
            raise ValueError("broker provider is disconnected")

    def _apply_fill(self, execution: Execution) -> None:
        existing = self._positions.get(execution.symbol)
        notional = execution.quantity * execution.price

        if execution.side is OrderSide.BUY:
            if notional > self._account.cash_balance:
                raise ValueError("insufficient cash")
            previous_quantity = existing.quantity if existing else Decimal("0")
            previous_cost = existing.quantity * existing.average_price if existing else Decimal("0")
            quantity = previous_quantity + execution.quantity
            self._positions[execution.symbol] = Position(
                symbol=execution.symbol,
                quantity=quantity,
                average_price=(previous_cost + notional) / quantity,
                updated_at=execution.executed_at,
            )
            cash_balance = self._account.cash_balance - notional
        else:
            if existing is None or execution.quantity > existing.quantity:
                raise ValueError("insufficient position")
            quantity = existing.quantity - execution.quantity
            if quantity == Decimal("0"):
                del self._positions[execution.symbol]
            else:
                self._positions[execution.symbol] = Position(
                    symbol=existing.symbol,
                    quantity=quantity,
                    average_price=existing.average_price,
                    updated_at=execution.executed_at,
                )
            cash_balance = self._account.cash_balance + notional

        self._account = Account(
            id=self._account.id,
            cash_balance=cash_balance,
            equity=self._account.equity,
            buying_power=cash_balance,
            updated_at=execution.executed_at,
            positions=self.get_positions(),
        )

    def _refresh_account(self, updated_at: datetime) -> None:
        market_value = sum(
            (position.quantity * self.MARKET_PRICE for position in self._positions.values()),
            start=Decimal("0"),
        )
        self._account = Account(
            id=self._account.id,
            cash_balance=self._account.cash_balance,
            equity=self._account.cash_balance + market_value,
            buying_power=self._account.cash_balance,
            updated_at=updated_at,
            positions=self.get_positions(),
        )
