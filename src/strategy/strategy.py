from abc import ABC, abstractmethod

from src.marketdata.models import OHLCV, Quote
from src.strategy.models import StrategyState, TradingSignal


class Strategy(ABC):
    """Interface for a strategy lifecycle and market-data events."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the strategy name."""
        raise NotImplementedError

    @property
    @abstractmethod
    def state(self) -> StrategyState:
        """Return the current strategy state."""
        raise NotImplementedError

    @abstractmethod
    def start(self) -> None:
        """Start the strategy."""
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> None:
        """Stop the strategy."""
        raise NotImplementedError

    @abstractmethod
    def on_quote(self, quote: Quote) -> TradingSignal | None:
        """Handle a quote and optionally produce a signal."""
        raise NotImplementedError

    @abstractmethod
    def on_bar(self, bar: OHLCV) -> TradingSignal | None:
        """Handle a bar and optionally produce a signal."""
        raise NotImplementedError
