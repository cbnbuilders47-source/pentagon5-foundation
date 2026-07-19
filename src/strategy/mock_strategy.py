from datetime import UTC, datetime

from src.marketdata.models import OHLCV, Quote
from src.strategy.models import StrategyState, StrategyStatus, TradingSignal
from src.strategy.strategy import Strategy


class MockStrategy(Strategy):
    """Strategy stub with lifecycle state and no trading logic."""

    def __init__(self) -> None:
        self._state = StrategyState(
            status=StrategyStatus.STOPPED,
            updated_at=datetime.now(UTC),
        )

    @property
    def name(self) -> str:
        """Return the mock strategy name."""
        return "MockStrategy"

    @property
    def state(self) -> StrategyState:
        """Return the current lifecycle state."""
        return self._state

    def start(self) -> None:
        """Set the strategy state to running."""
        self._state = StrategyState(
            status=StrategyStatus.RUNNING,
            updated_at=datetime.now(UTC),
        )

    def stop(self) -> None:
        """Set the strategy state to stopped."""
        self._state = StrategyState(
            status=StrategyStatus.STOPPED,
            updated_at=datetime.now(UTC),
        )

    def on_quote(self, quote: Quote) -> TradingSignal | None:
        """Ignore a quote without producing a signal."""
        return None

    def on_bar(self, bar: OHLCV) -> TradingSignal | None:
        """Ignore a bar without producing a signal."""
        return None
