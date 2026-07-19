from abc import ABC, abstractmethod
from datetime import UTC, datetime

from .models import OHLCV, Quote


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


class MockMarketDataProvider(MarketDataProvider):
    """Deterministic in-memory market data provider for tests."""

    def connect(self) -> None:
        pass

    def disconnect(self) -> None:
        pass

    def subscribe(self, symbol: str) -> None:
        pass

    def get_quote(self, symbol: str) -> Quote:
        return Quote(
            symbol=symbol,
            bid=100.00,
            ask=100.10,
            last_price=100.05,
            volume=1_000.0,
            timestamp=datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
        )

    def get_ohlcv(self, symbol: str) -> OHLCV:
        return OHLCV(
            symbol=symbol,
            open=99.50,
            high=101.00,
            low=99.00,
            close=100.05,
            volume=10_000.0,
            timestamp=datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
            interval="1m",
        )
