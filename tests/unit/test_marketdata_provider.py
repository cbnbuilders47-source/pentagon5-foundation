import pytest

from src.marketdata.models import OHLCV, Quote
from src.marketdata.provider import MockMarketDataProvider


@pytest.fixture
def provider() -> MockMarketDataProvider:
    return MockMarketDataProvider()


def test_get_quote(provider: MockMarketDataProvider) -> None:
    quote = provider.get_quote("AAPL")

    assert isinstance(quote, Quote)
    assert quote.symbol == "AAPL"
    assert quote.bid < quote.ask


def test_get_ohlcv(provider: MockMarketDataProvider) -> None:
    ohlcv = provider.get_ohlcv("AAPL")

    assert isinstance(ohlcv, OHLCV)
    assert ohlcv.symbol == "AAPL"
    assert ohlcv.interval == "1m"
