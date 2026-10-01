"""Price-data source interface.

The broker/exchange for historical data is NOT decided yet. Every source
(CSV files, an exchange API, MetaTrader 5 / FTMO later) implements this one
interface so the rest of the system never knows where candles came from.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from backtester.core.models import Candle, Timeframe


class DataAdapter(ABC):
    @abstractmethod
    def fetch(
        self, symbol: str, timeframe: Timeframe, start: datetime, end: datetime
    ) -> list[Candle]:
        """Return CLOSED candles with start <= ts < end, oldest first, timestamps in UTC."""
