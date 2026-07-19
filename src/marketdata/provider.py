from abc import ABC, abstractmethod


class MarketDataProvider(ABC):
    """Base interface for market data providers."""

    @abstractmethod
    def connect(self) -> None:
        """Connect to the market data source."""
        raise NotImplementedError

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the market data source."""
        raise NotImplementedError

    @abstractmethod
    def subscribe(self, symbol: str) -> None:
        """Subscribe to updates for a symbol."""
        raise NotImplementedError
