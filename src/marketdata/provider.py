from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote as url_quote

import httpx

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


class MarketDataProviderError(RuntimeError):
    """Raised when market data cannot be fetched or parsed."""


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


class YahooFinanceMarketDataProvider(MarketDataProvider):
    """Synchronous Yahoo Finance provider using its public JSON endpoints."""

    BASE_URL = "https://query1.finance.yahoo.com"

    def __init__(
        self,
        *,
        client: httpx.Client | None = None,
        timeout: float = 10.0,
    ) -> None:
        self._client = client
        self._timeout = timeout
        self._subscriptions: set[str] = set()

    def connect(self) -> None:
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.BASE_URL,
                timeout=self._timeout,
                headers={"User-Agent": "PENTAGON5/market-data"},
            )

    def disconnect(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    def subscribe(self, symbol: str) -> None:
        self._subscriptions.add(self._symbol(symbol))

    def get_quote(self, symbol: str) -> Quote:
        normalized = self._symbol(symbol)
        payload = self._get_json(
            "/v7/finance/quote",
            params={"symbols": normalized},
        )
        try:
            result = payload["quoteResponse"]["result"][0]
            return Quote(
                symbol=normalized,
                bid=self._number(result, "bid"),
                ask=self._number(result, "ask"),
                last_price=self._number(result, "regularMarketPrice"),
                volume=self._number(result, "regularMarketVolume"),
                timestamp=self._timestamp(result["regularMarketTime"]),
            )
        except (IndexError, KeyError, TypeError, ValueError) as error:
            raise MarketDataProviderError(
                f"Yahoo Finance returned invalid quote data for {normalized}"
            ) from error

    def get_ohlcv(self, symbol: str) -> OHLCV:
        normalized = self._symbol(symbol)
        payload = self._get_json(
            f"/v8/finance/chart/{url_quote(normalized, safe='')}",
            params={"range": "1d", "interval": "1m"},
        )
        try:
            result = payload["chart"]["result"][0]
            timestamps = result["timestamp"]
            values = result["indicators"]["quote"][0]
            index = self._latest_complete_index(timestamps, values)
            return OHLCV(
                symbol=normalized,
                open=self._array_number(values, "open", index),
                high=self._array_number(values, "high", index),
                low=self._array_number(values, "low", index),
                close=self._array_number(values, "close", index),
                volume=self._array_number(values, "volume", index),
                timestamp=self._timestamp(timestamps[index]),
                interval="1m",
            )
        except (IndexError, KeyError, TypeError, ValueError) as error:
            raise MarketDataProviderError(
                f"Yahoo Finance returned invalid OHLCV data for {normalized}"
            ) from error

    def _get_json(self, path: str, *, params: dict[str, str]) -> dict[str, Any]:
        self.connect()
        assert self._client is not None
        try:
            response = self._client.get(path, params=params)
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as error:
            raise MarketDataProviderError("Yahoo Finance request failed") from error
        if not isinstance(payload, dict):
            raise MarketDataProviderError("Yahoo Finance returned a malformed response")
        return payload

    @staticmethod
    def _symbol(symbol: str) -> str:
        normalized = symbol.strip().upper()
        if not normalized:
            raise ValueError("symbol must not be empty")
        return normalized

    @staticmethod
    def _number(values: dict[str, Any], key: str) -> float:
        value = values[key]
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise TypeError(f"{key} must be numeric")
        return float(value)

    @classmethod
    def _array_number(cls, values: dict[str, Any], key: str, index: int) -> float:
        items = values[key]
        if not isinstance(items, list):
            raise TypeError(f"{key} must be an array")
        return cls._number({"value": items[index]}, "value")

    @staticmethod
    def _timestamp(value: Any) -> datetime:
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise TypeError("timestamp must be numeric")
        return datetime.fromtimestamp(value, tz=UTC)

    @staticmethod
    def _latest_complete_index(timestamps: Any, values: Any) -> int:
        if not isinstance(timestamps, list) or not isinstance(values, dict):
            raise TypeError("OHLCV series must contain arrays")
        keys = ("open", "high", "low", "close", "volume")
        for index in range(len(timestamps) - 1, -1, -1):
            if all(
                isinstance(values.get(key), list)
                and index < len(values[key])
                and values[key][index] is not None
                for key in keys
            ):
                return index
        raise ValueError("OHLCV series has no complete candle")
