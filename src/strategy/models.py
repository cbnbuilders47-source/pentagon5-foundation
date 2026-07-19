from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum


class StrategyStatus(StrEnum):
    STOPPED = "stopped"
    RUNNING = "running"
    ERROR = "error"


class SignalType(StrEnum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass(frozen=True, slots=True)
class TradingSignal:
    symbol: str
    signal_type: SignalType
    generated_at: datetime
    quantity: Decimal
    reason: str

    def __post_init__(self) -> None:
        if self.signal_type in (SignalType.BUY, SignalType.SELL):
            if self.quantity <= Decimal("0"):
                raise ValueError("quantity must be positive for buy and sell signals")
        elif self.quantity < Decimal("0"):
            raise ValueError("quantity cannot be negative for hold signals")


@dataclass(frozen=True, slots=True)
class StrategyState:
    status: StrategyStatus
    updated_at: datetime
    last_signal: TradingSignal | None = None
    error_message: str | None = None
