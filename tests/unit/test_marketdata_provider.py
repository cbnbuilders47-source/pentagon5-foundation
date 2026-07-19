from collections.abc import Iterator

import httpx
import pytest

from src.marketdata.models import OHLCV, Quote
from src.marketdata.provider import (
    MarketDataProviderError,
    MockMarketDataProvider,
    YahooFinanceMarketDataProvider,
)


@pytest.fixture
def provider() -> MockMarketDataProvider:
    return MockMarketDataProvider()


@pytest.fixture
def yahoo_provider() -> Iterator[YahooFinanceMarketDataProvider]:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v7/finance/quote":
            return httpx.Response(
                200,
                json={
                    "quoteResponse": {
                        "result": [
                            {
                                "symbol": "AAPL",
                                "bid": 199.9,
                                "ask": 200.1,
                                "regularMarketPrice": 200.0,
                                "regularMarketVolume": 1_500_000,
                                "regularMarketTime": 1_735_732_800,
                            }
                        ]
                    }
                },
            )
        if request.url.path == "/v8/finance/chart/AAPL":
            return httpx.Response(
                200,
                json={
                    "chart": {
                        "result": [
                            {
                                "timestamp": [1_735_732_740, 1_735_732_800],
                                "indicators": {
                                    "quote": [
                                        {
                                            "open": [199.0, 200.0],
                                            "high": [201.0, None],
                                            "low": [198.5, None],
                                            "close": [200.0, None],
                                            "volume": [50_000, None],
                                        }
                                    ]
                                },
                            }
                        ]
                    }
                },
            )
        return httpx.Response(404)

    client = httpx.Client(
        base_url=YahooFinanceMarketDataProvider.BASE_URL,
        transport=httpx.MockTransport(handler),
    )
    provider = YahooFinanceMarketDataProvider(client=client)
    yield provider
    provider.disconnect()


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


def test_yahoo_get_quote(yahoo_provider: YahooFinanceMarketDataProvider) -> None:
    quote = yahoo_provider.get_quote("aapl")

    assert isinstance(quote, Quote)
    assert quote.symbol == "AAPL"
    assert quote.bid < quote.ask
    assert quote.last_price == 200.0


def test_yahoo_get_ohlcv(yahoo_provider: YahooFinanceMarketDataProvider) -> None:
    ohlcv = yahoo_provider.get_ohlcv("AAPL")

    assert isinstance(ohlcv, OHLCV)
    assert ohlcv.symbol == "AAPL"
    assert ohlcv.interval == "1m"
    assert ohlcv.close == 200.0


def test_yahoo_request_failure_is_wrapped() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(503)

    client = httpx.Client(
        base_url=YahooFinanceMarketDataProvider.BASE_URL,
        transport=httpx.MockTransport(handler),
    )
    provider = YahooFinanceMarketDataProvider(client=client)

    with pytest.raises(MarketDataProviderError, match="request failed"):
        provider.get_quote("AAPL")

    provider.disconnect()
