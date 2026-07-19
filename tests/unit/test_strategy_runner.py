from datetime import UTC, datetime
from decimal import Decimal

import pytest

from src.broker.models import (
    Account,
    Execution,
    Order,
    OrderRequest,
    OrderStatus,
    Position,
)
from src.broker.provider import BrokerProvider
from src.marketdata.models import OHLCV, Quote
from src.strategy.models import (
    SignalType,
    StrategyState,
    StrategyStatus,
    TradingSignal,
)
from src.strategy.runner import StrategyRunner
from src.strategy.strategy import Strategy


class StubStrategy(Strategy):
    """Controllable strategy used by StrategyRunner unit tests."""

    def __init__(
        self,
        quote_signal: TradingSignal | None = None,
        bar_signal: TradingSignal | None = None,
    ) -> None:
        self._state = StrategyState(
            status=StrategyStatus.STOPPED,
            updated_at=datetime.now(UTC),
        )
        self._quote_signal = quote_signal
        self._bar_signal = bar_signal

    @property
    def name(self) -> str:
        return "TestStrategy"

    @property
    def state(self) -> StrategyState:
        return self._state

    def start(self) -> None:
        self._state = StrategyState(
            status=StrategyStatus.RUNNING,
            updated_at=datetime.now(UTC),
        )

    def stop(self) -> None:
        self._state = StrategyState(
            status=StrategyStatus.STOPPED,
            updated_at=datetime.now(UTC),
        )

    def on_quote(self, quote: Quote) -> TradingSignal | None:
        return self._quote_signal

    def on_bar(self, bar: OHLCV) -> TradingSignal | None:
        return self._bar_signal


class RecordingBroker(BrokerProvider):
    """Broker test double that records submitted order requests."""

    def __init__(self) -> None:
        self.requests: list[OrderRequest] = []

    def connect(self) -> None:
        pass

    def disconnect(self) -> None:
        pass

    def is_connected(self) -> bool:
        return True

    def place_order(self, request: OrderRequest) -> Order:
        self.requests.append(request)
        return Order(
            id=f"order-{len(self.requests)}",
            symbol=request.symbol,
            side=request.side,
            order_type=request.order_type,
            quantity=request.quantity,
            status=OrderStatus.FILLED,
            created_at=request.requested_at,
            updated_at=request.requested_at,
            limit_price=request.limit_price,
        )

    def cancel_order(self, order_id: str) -> Order:
        raise NotImplementedError

    def get_order(self, order_id: str) -> Order:
        raise NotImplementedError

    def get_executions(
        self,
        order_id: str | None = None,
    ) -> tuple[Execution, ...]:
        return ()

    def get_positions(self) -> tuple[Position, ...]:
        return ()

    def get_account(self) -> Account:
        raise NotImplementedError


def make_signal(signal_type: SignalType) -> TradingSignal:
    quantity = Decimal("0") if signal_type is SignalType.HOLD else Decimal("2")
    return TradingSignal(
        symbol="AAPL",
        signal_type=signal_type,
        generated_at=datetime.now(UTC),
        quantity=quantity,
        reason="unit test",
    )


def make_quote() -> Quote:
    return Quote(
        symbol="AAPL",
        bid=99.0,
        ask=101.0,
        last_price=100.0,
        volume=1_000.0,
        timestamp=datetime.now(UTC),
    )


def make_bar() -> OHLCV:
    return OHLCV(
        symbol="AAPL",
        open=99.0,
        high=102.0,
        low=98.0,
        close=100.0,
        volume=5_000.0,
        timestamp=datetime.now(UTC),
        interval="1m",
    )


def test_start_and_stop_update_strategy_status() -> None:
    strategy = StubStrategy()
    runner = StrategyRunner(strategy, RecordingBroker())

    runner.start()

    running_status = strategy.state.status
    assert running_status == StrategyStatus.RUNNING

    runner.stop()

    stopped_status = strategy.state.status
    assert stopped_status == StrategyStatus.STOPPED


def test_stopped_strategy_rejects_events() -> None:
    runner = StrategyRunner(StubStrategy(), RecordingBroker())

    with pytest.raises(
        ValueError,
        match="strategy must be running to process events",
    ):
        runner.on_quote(make_quote())


def test_buy_signal_submits_market_buy_order() -> None:
    signal = make_signal(SignalType.BUY)
    strategy = StubStrategy(quote_signal=signal)
    broker = RecordingBroker()
    runner = StrategyRunner(strategy, broker)
    runner.start()

    order = runner.on_quote(make_quote())

    assert order is not None
    assert order.symbol == signal.symbol
    assert order.side.value == "buy"
    assert order.order_type.value == "market"
    assert order.quantity == signal.quantity
    assert broker.requests[0].requested_at == signal.generated_at


def test_sell_signal_submits_market_sell_order() -> None:
    signal = make_signal(SignalType.SELL)
    strategy = StubStrategy(bar_signal=signal)
    broker = RecordingBroker()
    runner = StrategyRunner(strategy, broker)
    runner.start()

    order = runner.on_bar(make_bar())

    assert order is not None
    assert order.symbol == signal.symbol
    assert order.side.value == "sell"
    assert order.order_type.value == "market"
    assert order.quantity == signal.quantity
    assert len(broker.requests) == 1


def test_hold_signal_does_not_submit_order() -> None:
    strategy = StubStrategy(quote_signal=make_signal(SignalType.HOLD))
    broker = RecordingBroker()
    runner = StrategyRunner(strategy, broker)
    runner.start()

    assert runner.on_quote(make_quote()) is None
    assert broker.requests == []


def test_none_signal_does_not_submit_order() -> None:
    strategy = StubStrategy()
    broker = RecordingBroker()
    runner = StrategyRunner(strategy, broker)
    runner.start()

    assert runner.on_bar(make_bar()) is None
    assert broker.requests == []
