"""Incremental daily regimes. Spec: regime-classifier.md > Rule (no lookahead)."""

from bisect import bisect_right
from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta
from itertools import pairwise
from math import isfinite
from zoneinfo import ZoneInfo

from backtester.core.models import Timeframe
from backtester.core.series import CandleSeries, SeriesView
from backtester.detectors.atr import Atr


@dataclass(frozen=True)
class RegimeConfig:
    timeframe: Timeframe = Timeframe.D1
    trend_method: str = "er"
    er_days: int = 20
    er_trend: float = 0.30
    adx_period: int = 14
    adx_trend: float = 20
    atr_period: int = 14
    vol_lookback_days: int = 500
    vol_high_rank: float = 0.5
    min_trades_best: int = 30

    def __post_init__(self):
        if self.timeframe is not Timeframe.D1 or self.trend_method not in ("er", "adx"):
            raise ValueError("regimes require D1 and er/adx")
        for name in ("er_days", "adx_period", "atr_period", "vol_lookback_days", "min_trades_best"):
            value = getattr(self, name)
            if type(value) is not int or value < 1:
                raise ValueError(f"{name} must be a positive integer")
        for name, upper in (("er_trend", 1), ("vol_high_rank", 1), ("adx_trend", 100)):
            value = getattr(self, name)
            if not isfinite(value) or not 0 <= value <= upper:
                raise ValueError(f"{name} must be between zero and {upper}")


@dataclass(frozen=True)
class RegimeLabel:
    regime_trend: str = "unknown"
    regime_vol: str = "unknown"


class _Rma:
    def __init__(self, period):
        self.period, self.count, self.total, self.value = period, 0, 0.0, None

    def update(self, value):
        self.count += 1
        if self.value is None:
            self.total += value
            if self.count == self.period:
                self.value = self.total / self.period
        else:
            self.value += (value - self.value) / self.period
        return self.value


class RegimeClassifier:
    """Receives only closed SeriesViews, once each in order; never revises labels."""

    def __init__(self, config=None):
        self.config = config or RegimeConfig()
        self.atr = Atr(self.config.atr_period)
        self._vols = []
        self._count = 0
        self._dm = [_Rma(self.config.adx_period) for _ in range(2)]
        self._adx = _Rma(self.config.adx_period)

    def update(self, view: SeriesView) -> RegimeLabel:
        cfg = self.config
        if view.timeframe is not cfg.timeframe or view.cursor != self._count:
            raise ValueError("regime updates require sequential D1 views")
        self._count += 1
        candle = view.current
        atr = self.atr.update(view)
        trend = vol = "unknown"
        if cfg.trend_method == "er" and len(view) > cfg.er_days:
            closes = [c.close for c in view.last(cfg.er_days + 1)]
            change = closes[-1] - closes[0]
            noise = sum(abs(b - a) for a, b in pairwise(closes))
            er = abs(change) / noise if noise else 0.0
            trend = self._trend(er >= cfg.er_trend and change != 0, change)
        if cfg.trend_method == "adx" and view.cursor:
            prev = view[-2]
            up, down = candle.high - prev.high, prev.low - candle.low
            plus = self._dm[0].update(up if up > down and up > 0 else 0)
            minus = self._dm[1].update(down if down > up and down > 0 else 0)
            if plus is not None:
                # The common smoothed TR divisor cancels in DX and DI comparison.
                dx = 100 * abs(plus - minus) / (plus + minus) if plus + minus else 0
                adx = self._adx.update(dx)
                if adx is not None:
                    trend = self._trend(adx >= cfg.adx_trend and plus != minus, plus - minus)
        measure = atr / candle.close if atr is not None and candle.close > 0 else None
        history = self._vols[-cfg.vol_lookback_days :]
        if measure is not None and len(history) == cfg.vol_lookback_days and None not in history:
            rank = sum(v <= measure for v in history) / len(history)
            vol = "high" if rank >= cfg.vol_high_rank else "low"
        self._vols.append(measure)
        return RegimeLabel(trend, vol)

    @staticmethod
    def _trend(trending, change):
        return ("trend_up" if change > 0 else "trend_down") if trending else "sideways"


NEW_YORK = ZoneInfo("America/New_York")


def _d1_close(ts: datetime) -> datetime:
    """Close of the D1 candle opening at `ts`. A 17:00 New York day lasts 23 or 25 hours on
    DST changes, so open + 24 h would make the 25-hour day's label usable an hour early
    (lookahead); the true close is 17:00 New York of the next day. Never earlier than 24 h."""
    local = ts.astimezone(NEW_YORK)
    if (local.hour, local.minute) != (17, 0):
        return ts + timedelta(days=1)
    close = datetime.combine(local.date() + timedelta(days=1), time(17), NEW_YORK)
    return max(close.astimezone(UTC), ts + timedelta(days=1))


class RegimeHistory:
    """Immutable daily labels, joined at close <= entry (including NY DST boundaries)."""

    def __init__(self, series, config=None):
        detector = RegimeClassifier(config)
        self._closes, self._labels = [], []
        for i in range(len(series)):
            view = series.view(i)
            self._labels.append(detector.update(view))
            self._closes.append(_d1_close(view.current.ts))

    def at(self, entry):
        if entry.utcoffset() is None:
            raise ValueError("entry time must be timezone aware")
        i = bisect_right(self._closes, entry) - 1
        return self._labels[i] if i >= 0 else RegimeLabel()


def label_trades(trades, sources, config=None):
    """One D1 adapter read per symbol, all available pre-entry history; no trade mutation."""
    trades = list(trades)
    cfg = config or RegimeConfig()
    histories = {}
    for symbol in sorted({t.symbol for t in trades}):
        entries = [t.entry_time for t in trades if t.symbol == symbol]
        end = max(entries)
        days = [d for d in sources.cached_days(symbol) if d <= end.date()]
        candles = []
        if days:
            start = datetime.combine(min(days), time(), UTC)
            if start < end:
                candles = sources.adapter(symbol).fetch(symbol, cfg.timeframe, start, end)
        histories[symbol] = RegimeHistory(CandleSeries(symbol, cfg.timeframe, candles), cfg)
    return [histories[t.symbol].at(t.entry_time) for t in trades]
