"""Incremental local-clock H1 events. Spec: strategy-h1-shock.md.

Only the current closed M1 is consumed. H1 prices require both boundary candles;
same-clock history is read before the current return is appended.
"""
from __future__ import annotations

import math
from collections import defaultdict, deque
from datetime import datetime, time, timedelta
from itertools import pairwise
from statistics import median
from zoneinfo import ZoneInfo

from backtester.core.models import Candle, Direction, Timeframe
from backtester.core.series import SeriesView
from backtester.detectors.settings import DetectorSettings
from backtester.strategy.base import Order, Strategy, UnsupportedSymbolError
from backtester.strategy.h1_shock.config import SYMBOLS, H1ShockConfig
from backtester.strategy.session_stats import TimedExit
from backtester.strategy.timed_hold.config import TimedHoldConfig
from backtester.strategy.timed_hold.day_filter import DayFilter

MINUTE = timedelta(minutes=1)
HOUR = timedelta(hours=1)


class H1Shock(Strategy):
    base_timeframe = Timeframe.M1
    timeframes = (Timeframe.M1,)
    uses_session_break_even = False

    def __init__(self, symbol: str, config: H1ShockConfig | None = None,
                 detectors: DetectorSettings | None = None):
        if symbol not in SYMBOLS:
            raise UnsupportedSymbolError(f"h1_shock supports {SYMBOLS}, got {symbol}")
        self.symbol = symbol
        self.config = cfg = config or H1ShockConfig()
        self._index = symbol in ("NAS100", "US500")
        self.zone = ZoneInfo("America/New_York" if self._index else "Europe/London")
        self._days = DayFilter(TimedHoldConfig(
            skip_nyse_short_days=self._index, calendar_dir=cfg.calendar_dir))
        self.min_warmup_days = max(cfg.warmup_days, cfg.same_clock_lookback * 2)
        self._window = defaultdict(lambda: deque(maxlen=cfg.same_clock_lookback))
        self._start: datetime | None = None
        self._bars: list[Candle] = []
        self._last_ts: datetime | None = None
        self._flat_price: float | None = None
        self._flat_count = 0
        self._stale = False
        self._duplicate = False
        self._atr: float | None = None
        self._prev_close: float | None = None
        self._seed: list[float] = []
        self._exit = TimedExit()
        self._exit_at: datetime | None = None
        self._active: dict | None = None
        self.cooldown_until: datetime | None = None
        self.signals: list[dict] = []

    def _interval(self, start: datetime, end: datetime, entry: bool) -> bool:
        a, b = start.astimezone(self.zone), end.astimezone(self.zone)
        midnight = datetime.combine(a.date(), time(), self.zone)
        tomorrow = datetime.combine(a.date() + timedelta(days=1), time(), self.zone)
        if (a.weekday() >= 5 or b.date() != a.date()
                or midnight.utcoffset() != tomorrow.utcoffset()):
            return False
        if self._index:
            lo, hi = (time(10), time(15, 30)) if entry else (time(9, 30), time(16))
            return self._days.qualifies(a.date()) and lo <= a.time() < b.time() <= hi
        return time(0) <= a.time() < b.time() <= time(21)

    def eligible_interval(self, start: datetime, end: datetime) -> bool:
        """Deterministic event + hold mask; never inspects future OHLC."""
        return self._interval(start, end, entry=True)

    def on_candle(self, now: datetime, views: dict[Timeframe, SeriesView | None]) -> list[Order]:
        view = views[self.base_timeframe]
        if view is None:
            return []
        c = view.current
        cfg = self.config
        gap = 0 if self._last_ts is None else int((c.ts - self._last_ts) / MINUTE) - 1
        flat = (c.open == c.high == c.low == c.close
                and self._interval(c.ts, now, entry=False))
        self._flat_count = (self._flat_count + 1 if flat and gap == 0
                            and c.close == self._flat_price else int(flat))
        self._flat_price = c.close if flat else None
        stale = self._flat_count >= cfg.stale_run_minutes
        if self._active is not None:
            defects = self._active["defects"]
            if gap > cfg.maximum_missing_run:
                defects.add("missing_run")
            if gap < 0:
                defects.add("duplicate_timestamp")
            if stale:
                defects.add("stale_run")
            if self._exit_at is not None and now > self._exit_at:
                defects.add("missing_exit")
        self._last_ts = c.ts
        if self._exit_at is not None:
            self._exit.check(now.astimezone(self.zone), self._exit_at.astimezone(self.zone).time())
            if now >= self._exit_at:
                self._active = None
                self._exit_at = None
        start = c.ts.replace(minute=0, second=0, microsecond=0)
        if start != self._start:
            self._start, self._bars = start, []
            self._stale = self._duplicate = False
        self._stale |= stale
        self._duplicate |= gap < 0
        self._bars.append(c)
        if now != start + HOUR:
            return []
        bars = self._bars
        if (not self._interval(start, now, entry=False) or self._stale or self._duplicate
                or len(bars) < cfg.minimum_m1_count or bars[0].ts != start
                or any((b.ts - a.ts) / MINUTE - 1 > cfg.maximum_missing_run
                       for a, b in pairwise(bars))
                or any(b.ts.second or b.ts.microsecond or min(b.open, b.low) <= 0 for b in bars)):
            return []
        high, low = max(b.high for b in bars), min(b.low for b in bars)
        tr = high - low
        if self._prev_close is not None:
            tr = max(tr, abs(high - self._prev_close), abs(low - self._prev_close))
        self._prev_close = c.close
        if self._atr is None:
            self._seed.append(tr)
            if len(self._seed) == cfg.atr_period_h1:
                self._atr = sum(self._seed) / cfg.atr_period_h1
        else:
            self._atr = (self._atr * (cfg.atr_period_h1 - 1) + tr) / cfg.atr_period_h1
        r = math.log(c.close / bars[0].open)
        window = self._window[start.astimezone(self.zone).hour]
        z = None
        if len(window) == cfg.same_clock_lookback:
            center = median(window)
            mad = median(abs(x - center) for x in window)
            if math.isfinite(mad) and mad > 0:
                z = (r - center) / (cfg.mad_scale * mad)
        window.append(r)
        end = now + cfg.holding_hours * HOUR
        if (z is None or not math.isfinite(z) or abs(z) < cfg.event_z_threshold or r == 0
                or self._atr is None or not math.isfinite(self._atr) or self._atr <= 0
                or not self.eligible_interval(start, end)
                or (self.cooldown_until is not None and now < self.cooldown_until)
                or self._active is not None):
            return []
        if self.signal_price_cost is None:
            raise RuntimeError("h1_shock requires engine-resolved signal costs")
        cost = self.signal_price_cost(self.symbol, now, c.close)
        if not math.isfinite(cost) or cost <= 0:
            return []
        multiple = abs(c.close - bars[0].open) / (2 * cost)
        if multiple < cfg.minimum_event_cost_multiple:
            return []
        bullish = (r > 0) == (cfg.response_mode == "CONTINUATION")
        direction = Direction.BULLISH if bullish else Direction.BEARISH
        sign = 1 if direction is Direction.BULLISH else -1
        self.cooldown_until = self._exit_at = end
        ref = self._exit.open(now.astimezone(self.zone).date())
        self._active = {"ref": ref, "signal_time": now, "scheduled_exit": end,
                        "event_return": r, "robust_z": z, "event_cost_multiple": multiple,
                        "clock_hour": start.astimezone(self.zone).hour,
                        "three_hour_eligible": self.eligible_interval(start, now + 3 * HOUR),
                        "defects": set()}
        self.signals.append(self._active)
        return [Order(direction, c.close, c.close - sign * cfg.stop_atr_multiplier * self._atr,
                      None, reason=f"H1 shock {cfg.response_mode}", ref=ref)]

    def exits(self) -> list[object]:
        return self._exit.take()

    def on_order_skipped(self, ref: object, now: datetime) -> None:
        self._exit.forget(ref)
        if self._active is not None and self._active["ref"] == ref:
            self._active["skipped"] = True
            self._active = self._exit_at = self.cooldown_until = None

    def on_trade_closed(self, ref: object, result) -> None:
        self._exit.forget(ref)
        if self._active is not None and self._active["ref"] == ref:
            if result is not None:
                # Stops are processed before on_candle, so include their resolving minute.
                defects = self._active["defects"]
                if (self._last_ts is not None and
                        (result.exit_candle - self._last_ts) / MINUTE - 1
                        > self.config.maximum_missing_run):
                    defects.add("missing_run")
                if (self._exit_at is not None and
                        (result.exit_time > self._exit_at or
                         (result.exit_reason.value == "end_of_data"
                          and result.exit_time < self._exit_at))):
                    defects.add("missing_exit")
            self._active = None

    def session_records(self, run_end: datetime | None = None) -> list[dict]:
        return [{**r, "symbol": self.symbol,
                 "session": "h1_shock",
                 "trading_date": r["signal_time"].astimezone(self.zone).date().isoformat(),
                 "start": (r["signal_time"] - HOUR).isoformat(),
                 "end": r["scheduled_exit"].isoformat(),
                 "defects": sorted(r["defects"]),
                 "integrity_failed": bool(r["defects"])} for r in self.signals]
