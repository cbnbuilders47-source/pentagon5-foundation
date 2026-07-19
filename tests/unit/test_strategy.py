from datetime import UTC, datetime

import pytest

from src.marketdata.models import OHLCV, Quote
from src.strategy.mock_strategy import MockStrategy
from src.strategy.models import StrategyStatus


@pytest.fixture
def strategy() -> MockStrategy:
    return MockStrategy()


def test_initial_state_and_name(strategy: MockStrategy) -> None:
    assert strategy.state.status is StrategyStatus.STOPPED
    assert strategy.name == "MockStrategy"


def test_start_changes_state_to_running(strategy: MockStrategy) -> None:
    strategy.start()

    assert strategy.state.status is StrategyStatus.RUNNING


def test_stop_changes_state_to_stopped(strategy: MockStrategy) -> None:
    strategy.start()
    strategy.stop()

    assert strategy.state.status is StrategyStatus.STOPPED


def test_on_quote_returns_none(strategy: MockStrategy) -> None:
    quote = Quote(
        symbol="AAPL",
        bid=199.90,
        ask=200.10,
        last_price=200.00,
        volume=1_000.0,
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert strategy.on_quote(quote) is None


def test_on_bar_returns_none(strategy: MockStrategy) -> None:
    bar = OHLCV(
        symbol="AAPL",
        open=199.00,
        high=201.00,
        low=198.50,
        close=200.00,
        volume=50_000.0,
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        interval="1m",
    )

    assert strategy.on_bar(bar) is None
