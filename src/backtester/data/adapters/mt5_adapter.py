"""Candles from a running MetaTrader 5 terminal (FTMO's feed). Spec: ARCHITECTURE.md ›
MetaTrader 5, ROADMAP.md › 0.4.

The `MetaTrader5` package is optional (extra `[mt5]`, Windows only) and is imported only
here (`load_mt5`); everything else gets the module passed in, so tests use a fake one.
The adapter needs a connected terminal (`live/connection.py` `session`).

- **Server time → UTC.** MT5 bar times are the broker's server wall clock written as if it
  were UTC. `ServerClock` says how that clock relates to UTC: server time = local time in
  an IANA `zone` + `shift_hours` (e.g. `America/New_York` + 7 h: UTC+2 in winter, UTC+3 while
  New York has summer time). The rule is measured, never assumed (`tools/mt5_info.py`).
- **Only closed candles:** a bar whose UTC close time is after `now` is dropped (the
  forming one).
- **Spread:** MT5's per-bar spread in points × the symbol's point, in price units
  (`Candle.spread`). Real FTMO spreads, unlike histdata's (none).
- **Symbol mapping:** our names (XAUUSD) → the broker's (e.g. with a suffix), a setting.
"""

from __future__ import annotations

import importlib
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from types import MappingProxyType, ModuleType
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from backtester.core.models import Candle, Timeframe
from backtester.data.adapters.base import DataAdapter
from backtester.data.adapters.cache_adapter import candles_from_frame

# Timeframes the adapter serves: they divide an hour or are one, so server and UTC bars
# have the same boundaries. H4 / D1 bars are cut on the server's day, not ours.
TIMEFRAME_NAMES = {
    Timeframe.M1: "TIMEFRAME_M1",
    Timeframe.M5: "TIMEFRAME_M5",
    Timeframe.M15: "TIMEFRAME_M15",
    Timeframe.M30: "TIMEFRAME_M30",
    Timeframe.H1: "TIMEFRAME_H1",
}
COLUMNS = ["ts", "open", "high", "low", "close", "volume", "spread"]
EPOCH = datetime(1970, 1, 1, tzinfo=UTC)


class Mt5Unavailable(RuntimeError):
    """The MetaTrader5 package isn't installed (it needs Windows: pip install -e ".[mt5]")."""


class Mt5Error(RuntimeError):
    """A call to the terminal failed; the message has MT5's error text."""


def load_mt5() -> ModuleType:
    try:
        return importlib.import_module("MetaTrader5")
    except ImportError as e:
        raise Mt5Unavailable(
            'the MetaTrader5 package is not installed (Windows only): pip install -e ".[mt5]"'
        ) from e


@dataclass(frozen=True)
class ServerClock:
    """Server wall time = local time in `zone` + `shift_hours`."""

    zone: str = "UTC"
    shift_hours: int = 0

    @property
    def label(self) -> str:
        sign = "+" if self.shift_hours >= 0 else "−"
        shift = f" {sign} {abs(self.shift_hours)} h" if self.shift_hours else ""
        return f"{self.zone}{shift}"

    def offset_at(self, utc: datetime) -> timedelta:
        """Server time − UTC at the UTC moment `utc`."""
        local = utc.astimezone(ZoneInfo(self.zone))
        return local.utcoffset() + timedelta(hours=self.shift_hours)

    def to_server(self, utc: datetime) -> datetime:
        """The server wall time at `utc`, as a UTC-tagged datetime (MT5's convention)."""
        return (utc + self.offset_at(utc)).replace(tzinfo=UTC)

    def to_utc(self, server_seconds) -> pd.DatetimeIndex:
        """UTC times of MT5 bar times (server seconds). In the hour a DST change repeats
        (never during trading) the first one is taken."""
        seconds = np.asarray(server_seconds, dtype="int64") - self.shift_hours * 3600
        local = pd.to_datetime(seconds, unit="s")
        if self.zone == "UTC":
            return local.tz_localize("UTC")
        aware = local.tz_localize(
            self.zone, ambiguous=np.ones(len(local), dtype=bool), nonexistent="shift_forward"
        )
        return aware.tz_convert("UTC")

    def to_dict(self) -> dict:
        return {"zone": self.zone, "shift_hours": self.shift_hours}

    @classmethod
    def from_dict(cls, data: Mapping | None) -> ServerClock | None:
        if not data:
            return None
        return cls(str(data["zone"]), int(data["shift_hours"]))


def mt5_timeframe(mt5: ModuleType, timeframe: Timeframe) -> int:
    if timeframe not in TIMEFRAME_NAMES:
        served = ", ".join(tf.name for tf in TIMEFRAME_NAMES)
        raise ValueError(f"{timeframe.name} is not served by the MT5 adapter ({served})")
    return getattr(mt5, TIMEFRAME_NAMES[timeframe])


def rates_frame(rates, point: float) -> pd.DataFrame:
    """MT5 rates (structured array) → columns time (server seconds), OHLC, volume (ticks),
    spread (price units)."""
    if rates is None or len(rates) == 0:
        return pd.DataFrame(columns=["time", "open", "high", "low", "close", "volume", "spread"])
    frame = pd.DataFrame(rates)
    return pd.DataFrame(
        {
            "time": frame["time"].astype("int64"),
            "open": frame["open"].astype(float),
            "high": frame["high"].astype(float),
            "low": frame["low"].astype(float),
            "close": frame["close"].astype(float),
            "volume": frame["tick_volume"].astype(float),
            "spread": frame["spread"].astype(float) * point,
        }
    )


def _utc(dt: datetime) -> datetime:
    return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)


class Mt5Adapter(DataAdapter):
    """`DataAdapter` over a connected terminal. `symbols`: our name → broker's name
    (missing names are used as they are)."""

    def __init__(
        self,
        mt5: ModuleType,
        clock: ServerClock,
        symbols: Mapping[str, str] | None = None,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ):
        if clock is None:
            raise ValueError(
                "the server time rule is not known yet: run python -m backtester.tools.mt5_info"
            )
        self.mt5 = mt5
        self.clock = clock
        self.symbols = MappingProxyType(dict(symbols or {}))
        self.now = now

    def broker_symbol(self, symbol: str) -> str:
        return self.symbols.get(symbol, symbol)

    def point(self, symbol: str) -> float:
        name = self.broker_symbol(symbol)
        self.mt5.symbol_select(name, True)
        info = self.mt5.symbol_info(name)
        if info is None:
            raise Mt5Error(f"{name}: unknown symbol on this server ({self._error()})")
        return float(info.point)

    def raw_frame(
        self, symbol: str, timeframe: Timeframe, server_from: datetime, server_to: datetime
    ) -> pd.DataFrame:
        """Bars between two server wall times (inclusive), times left in server seconds."""
        name = self.broker_symbol(symbol)
        point = self.point(symbol)
        rates = self.mt5.copy_rates_range(
            name, mt5_timeframe(self.mt5, timeframe), server_from, server_to
        )
        if rates is None:
            raise Mt5Error(f"{name} {timeframe.name}: no bars ({self._error()})")
        return rates_frame(rates, point)

    def to_candles(self, raw: pd.DataFrame, timeframe: Timeframe) -> pd.DataFrame:
        """Server-time bars → UTC candles (columns `COLUMNS`), closed ones only."""
        if raw.empty:
            return pd.DataFrame(columns=COLUMNS)
        out = raw.drop(columns="time")
        out.insert(0, "ts", self.clock.to_utc(raw["time"].to_numpy()))
        closed = out["ts"] + timeframe.duration <= pd.Timestamp(self.now())
        return out[closed].reset_index(drop=True)[COLUMNS]

    def fetch_frame(
        self, symbol: str, timeframe: Timeframe, start: datetime, end: datetime
    ) -> pd.DataFrame:
        start, end = _utc(start), _utc(end)
        if end <= start:
            raise ValueError(f"end {end} must be after start {start}")
        pad = timedelta(days=1)  # the server-time window around the UTC one
        raw = self.raw_frame(
            symbol, timeframe, self.clock.to_server(start - pad), self.clock.to_server(end + pad)
        )
        candles = self.to_candles(raw, timeframe)
        keep = (candles["ts"] >= pd.Timestamp(start)) & (candles["ts"] < pd.Timestamp(end))
        return candles[keep].reset_index(drop=True)

    def fetch(
        self, symbol: str, timeframe: Timeframe, start: datetime, end: datetime
    ) -> list[Candle]:
        return candles_from_frame(self.fetch_frame(symbol, timeframe, start, end))

    def history(self, symbol: str, timeframe: Timeframe) -> pd.DataFrame:
        """Every closed candle the terminal has for `symbol` / `timeframe` (the depth is the
        broker's and the terminal's "Max bars in chart"), UTC."""
        far = self.clock.to_server(self.now() + timedelta(days=1))
        raw = self.raw_frame(symbol, timeframe, EPOCH + timedelta(days=1), far)
        return self.to_candles(raw, timeframe)

    def _error(self) -> str:
        code, text = self.mt5.last_error()
        return f"MT5: {text} ({code})"
