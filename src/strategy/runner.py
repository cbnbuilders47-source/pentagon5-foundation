from src.broker.models import Order, OrderRequest, OrderSide, OrderType
from src.broker.provider import BrokerProvider
from src.marketdata.models import OHLCV, Quote
from src.strategy.models import SignalType, StrategyStatus, TradingSignal
from src.strategy.strategy import Strategy


class StrategyRunner:
    """Coordinate strategy events with broker order submission."""

    def __init__(self, strategy: Strategy, broker: BrokerProvider) -> None:
        self._strategy = strategy
        self._broker = broker

    def start(self) -> None:
        """Start the strategy."""
        self._strategy.start()

    def stop(self) -> None:
        """Stop the strategy."""
        self._strategy.stop()

    def on_quote(self, quote: Quote) -> Order | None:
        """Process a quote and submit any resulting order."""
        self._require_running()
        return self._submit_signal(self._strategy.on_quote(quote))

    def on_bar(self, bar: OHLCV) -> Order | None:
        """Process a bar and submit any resulting order."""
        self._require_running()
        return self._submit_signal(self._strategy.on_bar(bar))

    def _require_running(self) -> None:
        if self._strategy.state.status is not StrategyStatus.RUNNING:
            raise ValueError("strategy must be running to process events")

    def _submit_signal(self, signal: TradingSignal | None) -> Order | None:
        if signal is None or signal.signal_type is SignalType.HOLD:
            return None

        side = OrderSide.BUY if signal.signal_type is SignalType.BUY else OrderSide.SELL
        request = OrderRequest(
            symbol=signal.symbol,
            side=side,
            order_type=OrderType.MARKET,
            quantity=signal.quantity,
            requested_at=signal.generated_at,
        )
        return self._broker.place_order(request)
