from datetime import UTC, datetime
from decimal import Decimal

import pytest

from src.broker.models import OrderRequest, OrderSide, OrderStatus, OrderType
from src.broker.provider import MockBrokerProvider


@pytest.fixture
def provider() -> MockBrokerProvider:
    return MockBrokerProvider()


def market_buy_request() -> OrderRequest:
    return OrderRequest(
        symbol="AAPL",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=Decimal("10"),
        requested_at=datetime(2026, 1, 1, tzinfo=UTC),
    )


def test_connect_disconnect_and_connection_state(provider: MockBrokerProvider) -> None:
    assert provider.is_connected() is False

    provider.connect()
    assert provider.is_connected() is True

    provider.disconnect()
    assert provider.is_connected() is False


def test_market_buy_fills_and_updates_account(provider: MockBrokerProvider) -> None:
    provider.connect()
    starting_cash = provider.get_account().cash_balance

    order = provider.place_order(market_buy_request())

    assert order.status is OrderStatus.FILLED
    assert order.side is OrderSide.BUY
    assert order.order_type is OrderType.MARKET
    assert order.quantity == Decimal("10")
    assert provider.get_account().cash_balance == starting_cash - Decimal("1000")

    positions = provider.get_positions()
    assert len(positions) == 1
    assert positions[0].symbol == "AAPL"
    assert positions[0].quantity == Decimal("10")
    assert positions[0].average_price == Decimal("100")

    assert provider.get_order(order.id) == order
    executions = provider.get_executions(order.id)
    assert len(executions) == 1
    assert executions[0].order_id == order.id
    assert executions[0].price == Decimal("100")


def test_cancel_filled_market_order_is_rejected(provider: MockBrokerProvider) -> None:
    provider.connect()
    order = provider.place_order(market_buy_request())

    with pytest.raises(ValueError, match="only pending orders can be cancelled"):
        provider.cancel_order(order.id)

    assert provider.get_order(order.id).status is OrderStatus.FILLED


def test_place_order_while_disconnected_raises(provider: MockBrokerProvider) -> None:
    with pytest.raises(ValueError, match="disconnected"):
        provider.place_order(market_buy_request())


def test_limit_order_is_not_supported(provider: MockBrokerProvider) -> None:
    provider.connect()
    request = OrderRequest(
        symbol="AAPL",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        quantity=Decimal("10"),
        requested_at=datetime(2026, 1, 1, tzinfo=UTC),
        limit_price=Decimal("99"),
    )

    with pytest.raises(NotImplementedError, match="market orders only"):
        provider.place_order(request)
