from abc import ABC, abstractmethod

from src.broker.models import Account, Execution, Order, OrderRequest, Position


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
