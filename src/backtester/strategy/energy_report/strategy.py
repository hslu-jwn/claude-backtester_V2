"""Causal close-based reaction, adapted from _template.

Spec: strategy-energy_report.md > Daily ATR; Entry, stop and exit.
Only the latest closed candle of the supplied SeriesView is consumed.
"""
from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from math import isfinite
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from backtester.core.models import Direction, Timeframe
from backtester.core.series import SeriesView
from backtester.detectors.settings import DetectorSettings
from backtester.strategy.base import Order, Strategy, UnsupportedSymbolError
from backtester.strategy.energy_report.calendar import ReportCalendar
from backtester.strategy.energy_report.config import EnergyReportConfig
from backtester.strategy.session_stats import SessionStats, TimedExit

if TYPE_CHECKING:
    from backtester.engine.trade import TradeResult

NY = ZoneInfo("America/New_York")
ROLLOVER = time(17)
REFERENCE = time(10, 29)
ENTRY = time(10, 45)


class EnergyReport(Strategy):
    base_timeframe = Timeframe.M1
    timeframes = (Timeframe.M1,)
    uses_session_break_even = False

    def __init__(self, symbol: str, config: EnergyReportConfig | None = None,
                 detectors: DetectorSettings | None = None):
        if symbol not in ("USOIL", "UKOIL"):
            raise UnsupportedSymbolError(f"energy_report supports USOIL/UKOIL, got {symbol}")
        self.symbol = symbol
        self.config = config or EnergyReportConfig()
        self.detectors = detectors or DetectorSettings()
        self.min_warmup_days = max(60, self.config.atr_period * 4)
        self._calendar = ReportCalendar(self.config.calendar_dir)
        self._stats = SessionStats(time(), time(23, 59), self.config.atr_period)
        self._exit = TimedExit()
        self._exit_time = time(14, 30) if self.config.family == "F" else time(13)
        self._day: date | None = None
        self._reference: float | None = None
        self._attempted: date | None = None
        self._last_now: datetime | None = None
        self._active: dict | None = None
        self._records: list[dict] = []

    def on_candle(self, now: datetime, views: dict[Timeframe, SeriesView | None]) -> list[Order]:
        view = views[self.base_timeframe]
        if view is None:
            return []
        c = view.current
        if c.ts + self.base_timeframe.duration != now:
            raise ValueError("now must be the current M1 candle close")
        if self._last_now is not None and now <= self._last_now:
            raise ValueError("energy_report requires increasing closed candles")
        self._last_now = now
        local = now.astimezone(NY)
        self._exit.check(local, self._exit_time)
        if self._active is not None and now > self._active["scheduled_exit"]:
            self._active["defects"].add("missing_exit")

        # Rotate (17:00, next 17:00] onto a synthetic clock ending 23:59.
        day = local.date() + timedelta(days=int(local.time() > ROLLOVER))
        if day.weekday() < 5:
            rotated = (local - timedelta(hours=17, minutes=1)).time()
            self._stats.take_in(day, rotated, c)
            if local.time() == ROLLOVER:
                self._stats.finish()
        else:
            self._stats.finish()

        if local.date() != self._day:
            self._day, self._reference = local.date(), None
        if local.time() in (REFERENCE, ENTRY):
            prices = (c.open, c.high, c.low, c.close)
            valid = (all(isfinite(x) and x > 0 for x in prices)
                     and c.low <= min(c.open, c.close) <= max(c.open, c.close) <= c.high)
            if not valid:
                self._reference = None
                self._records.append({"ref": None, "signal_time": now, "scheduled_exit": now,
                                      "reaction": None, "atr": None, "skipped": True,
                                      "defects": {"invalid_signal_candle"}})
                return []
        if local.time() == REFERENCE:
            self._reference = c.close
        if (local.time() != ENTRY or self._attempted == local.date()
                or self._active is not None or self._reference is None
                or not self._calendar.qualifies(local.date(), self.config.days)):
            return []
        self._attempted = local.date()
        atr = self._stats.atr
        reaction = c.close - self._reference
        if (atr is None or not isfinite(atr) or atr <= 0 or reaction == 0
                or abs(reaction) < self.config.k * atr):
            return []
        bullish = (reaction > 0) == (self.config.family == "F")
        direction = Direction.BULLISH if bullish else Direction.BEARISH
        sign = 1 if direction is Direction.BULLISH else -1
        ref = self._exit.open(local.date())
        target = datetime.combine(local.date(), self._exit_time, NY).astimezone(UTC)
        self._active = {"ref": ref, "signal_time": now, "scheduled_exit": target,
                        "reaction": reaction, "atr": atr, "defects": set(), "skipped": False}
        self._records.append(self._active)
        return [Order(direction, c.close, c.close - sign * self.config.stop_atr * atr,
                      None, reason=f"Energy report {self.config.family} {self.config.days}", ref=ref)]

    def exits(self) -> list[object]:
        return self._exit.take()

    def on_order_skipped(self, ref: object, now: datetime) -> None:
        self._exit.forget(ref)
        if self._active is not None and self._active["ref"] == ref:
            self._active["skipped"] = True
            self._active = None

    def on_trade_closed(self, ref: object, result: TradeResult) -> None:
        self._exit.forget(ref)
        if self._active is None or self._active["ref"] != ref:
            return
        record = self._active
        if (result.exit_time > record["scheduled_exit"]
                or (result.exit_reason.value == "end_of_data"
                    and result.exit_time < record["scheduled_exit"])):
            record["defects"].add("missing_exit")
        rollover = datetime.combine(record["signal_time"].astimezone(NY).date(), ROLLOVER, NY)
        if result.exit_time >= rollover:
            record["defects"].add("unexpected_rollover")
        self._active = None

    def session_records(self, run_end: datetime | None = None) -> list[dict]:
        """Scheduled-exit defects supplement the coordinator's M1 integrity gate."""
        return [{"symbol": self.symbol, "session": "energy_report", "ref": r["ref"],
                 "trading_date": r["signal_time"].astimezone(NY).date().isoformat(),
                 "start": r["signal_time"].isoformat(), "end": r["scheduled_exit"].isoformat(),
                 "reaction": r["reaction"], "atr": r["atr"], "skipped": r["skipped"],
                 "defects": sorted(r["defects"]), "integrity_failed": bool(r["defects"])}
                for r in self._records]
