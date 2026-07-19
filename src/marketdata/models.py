from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Quote:
    symbol: str
    bid: float
    ask: float
    last_price: float
    volume: float
    timestamp: datetime


@dataclass(frozen=True)
class OHLCV:
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    timestamp: datetime
    interval: str
