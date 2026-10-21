"""No-wick retest study: many variants of "no-wick candle, limit at its open" scored fast.

    python -m backtester.tools.no_wick_retest_study --start 2015-01-01 --end 2021-09-13 \\
        --timeframes M5 M15 M30 H1 --workers 4 --out results/no_wick_retest/2026-10-21
    python -m backtester.tools.no_wick_retest_study --score --out results/no_wick_retest/2026-10-21

Research only: it changes no setting and no strategy (strategy 3 is `strategy/no_wick/`).

Signal (entry timeframe TF = M5 / M15 / M30 / H1, resampled from M1): a green candle whose
lower wick is at most `max_wick_share` of its range (variants 0.0 and 0.05), a red candle with
no upper wick mirrored. Every such candle is recorded with its filter flags, so one run scores
all trend and session variants:
  trend  none | bos | bos_clean | bos_4h (see `scan_signals`)
  session  all | pdf (signals closing 09:30-10:30, 15:00-17:00 or 19:00-22:00 New York skipped)
Entry: limit at the signal candle's open, placed at its close, valid for `expiry_candles` TF
candles, filled on M1 (gap through the level = fill at the M1 open; open at / beyond the stop =
that stop variant is dropped). Stops: swing 10 / 25 / 50 %, previous swing, previous candle,
ATR x 0.5 / 1 / 1.5 / 2. Targets: 0.5 .. 3 R, the last swing, none (time exit only).
Every trade is closed at the M1 close of 16:55 New York of its day (the next day when filled
after it), or at the last bar before a data gap over 2 h. No swap is charged. Within an M1
bar the stop comes first; the fill bar's own favourable side is never counted.

Per fill x stop variant one row of `trades.parquet` (stop, MFE before the stop, exit R, cost in
R, swing target R, flags), so new targets and filters score without re-running; `--score`
recomputes `summary.csv` from it. Costs: the engine's default `CostConfig` (spread, price
scaled, + commission) divided by the stop distance, net = gross - cost. `counts.csv`: signals,
filled, expired, gap-dropped orders per symbol and timeframe.

Order of events and conservative choices are in the functions' docstrings. Trades overlap, so
the t-stat is a rough guide only. Spec: strategy-no-wick.md (study of its body_end entry mode).
"""

from __future__ import annotations

import argparse
import math
import os
from collections.abc import Sequence
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from backtester.core.models import Candle, Direction, Timeframe
from backtester.core.mtf import HigherTimeframeClock
from backtester.core.series import CandleSeries
from backtester.data.sources import DEFAULT_SOURCES
from backtester.detectors.atr import Atr
from backtester.detectors.bos import BROKEN_KIND, BosDetector, breaks
from backtester.detectors.settings import DetectorSettings
from backtester.detectors.swings import SwingDetector, SwingKind, SwingPoint
from backtester.engine.costs import CostConfig
from backtester.paths import RESULTS_DIR
from backtester.strategy.no_wick.strategy import Structure, wick_share

NY = ZoneInfo("America/New_York")
NS = 1_000_000_000
SYMBOLS = (
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD", "EURJPY", "GBPJPY",
    "EURGBP", "XAUUSD", "XAGUSD", "NAS100", "US500", "GER40", "UK100", "JP225", "EU50",
)  # fmt: skip
MARKED_SYMBOLS = ("XAUUSD",)  # the development symbol of the other strategies: printed marked
TIMEFRAMES = (Timeframe.M5, Timeframe.M15, Timeframe.M30, Timeframe.H1)
TRENDS = ("none", "bos", "bos_clean", "bos_4h")
SESSIONS = ("all", "pdf")
GROUPS = {
    **dict.fromkeys(("EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD",
                     "EURJPY", "GBPJPY", "EURGBP"), "fx"),
    **dict.fromkeys(("NAS100", "US500", "US30", "US2000", "GER40", "UK100", "JP225", "EU50"),
                    "indices"),
    **dict.fromkeys(("XAUUSD", "XAGUSD"), "metals"),
}  # fmt: skip
START = date(2015, 1, 1)
END = date(2021, 9, 13)  # the day before the MT5 data cut-off (CLAUDE.md > data split)
TREND_BITS = {"none": 0, "bos": 1, "bos_clean": 2, "bos_4h": 4}


@dataclass(frozen=True, slots=True)
class StopSpec:
    name: str
    kind: str  # swing | prevswing | prevcandle | atr
    value: float  # buffer share of entry -> swing, or ATR multiple


STOP_SPECS = (
    StopSpec("swing10", "swing", 0.10),
    StopSpec("swing25", "swing", 0.25),
    StopSpec("swing50", "swing", 0.50),
    StopSpec("prevswing10", "prevswing", 0.10),
    StopSpec("prevcandle", "prevcandle", 0.0),
    StopSpec("atr0.5", "atr", 0.5),
    StopSpec("atr1", "atr", 1.0),
    StopSpec("atr1.5", "atr", 1.5),
    StopSpec("atr2", "atr", 2.0),
)  # the module docstring's "swing10 .. atr2"; names are the keys of the output


@dataclass(frozen=True, slots=True)
class StudyConfig:
    max_wick_share: float = 0.05  # widest wick recorded; narrower variants are scored later
    wick_variants: tuple[float, ...] = (0.0, 0.05)
    expiry_candles: int = 5  # a limit order waits this many TF candles
    atr_period: int = 14
    min_swing_target_r: float = 0.5  # the swing target needs at least this many R of room
    exit_time: time = time(16, 55)  # New York, before the 17:00 rollover (no swap)
    gap_hours: float = 2.0  # a hole in the M1 data longer than this ends open trades
    pdf_windows: tuple[tuple[time, time], ...] = (
        (time(9, 30), time(10, 30)),  # New York open
        (time(15, 0), time(17, 0)),  # late New York
        (time(19, 0), time(22, 0)),  # first three hours of Asia
    )  # New York time, start included, end excluded
    stops: tuple[StopSpec, ...] = STOP_SPECS
    targets: tuple[float, ...] = (0.5, 0.75, 1.0, 1.5, 2.0, 3.0)  # R from the fill price
    # scoring only: skip trades a trader would not take; both are known at the fill
    max_cost_r: float | None = 0.3  # spread + commission above this share of the risk (tiny stops)
    drop_overnight: bool = True  # held across the 17:00 rollover, swap is not modelled
    first_half_end_year: int = 2017  # halves: 2015-2017 / 2018 on
    min_trades: int = 300  # variants shown in the top list
    top: int = 20

    def __post_init__(self) -> None:
        if not 0 <= self.max_wick_share < 1:
            raise ValueError("max_wick_share must be >= 0 and < 1")
        if tuple(sorted(self.wick_variants)) != self.wick_variants:
            raise ValueError("wick_variants must be ascending")
        if self.wick_variants and self.wick_variants[-1] > self.max_wick_share:
            raise ValueError("wick_variants must not exceed max_wick_share")
        if self.expiry_candles < 1:
            raise ValueError("expiry_candles must be >= 1")


# --- signals -----------------------------------------------------------------------------------


def no_wick_direction(candle: Candle, max_share: float) -> tuple[Direction, float] | None:
    """(direction, wick share) when `candle` is a no-wick candle: green with a lower wick of at
    most `max_share` of its range (long), red with the same upper wick (short). No colour (open =
    close) or no range = None."""
    if candle.high <= candle.low or candle.close == candle.open:
        return None
    direction = Direction.BULLISH if candle.close > candle.open else Direction.BEARISH
    share = wick_share(direction, candle)
    return (direction, share) if share <= max_share else None


def in_pdf_window(close_time: datetime, cfg: StudyConfig) -> bool:
    """True when a candle closing at `close_time` falls into a skipped New York window."""
    local = close_time.astimezone(NY).time()
    return any(start <= local < end for start, end in cfg.pdf_windows)


def clean_structure(direction: Direction, highs: Sequence[float], lows: Sequence[float]) -> bool:
    """Long: the last two confirmed swing highs rise and the last two swing lows rise; short:
    both fall. Fewer than two of either kind, or mixed = False."""
    if len(highs) < 2 or len(lows) < 2:
        return False
    sign = 1 if direction is Direction.BULLISH else -1
    return sign * (highs[-1] - highs[-2]) > 0 and sign * (lows[-1] - lows[-2]) > 0


def four_hour_ok(
    direction: Direction, h4_trend: Direction | None, last_breaks: Sequence[Direction]
) -> bool:
    """The 4h trend agrees, or the last two structure breaks on the entry timeframe are both
    in the trade direction (see `BreakTracker`)."""
    return h4_trend is direction or list(last_breaks)[-2:] == [direction, direction]


class BreakTracker:
    """Every close beyond the open swing (confluences.md > BOS), in order, also the ones WITH
    the trend that the BOS detector discards: its BOS directions alternate, so two BOS in a row
    in one direction never happen, only a BOS followed by continuation breaks. Same used-up
    rule as `BosDetector`: a swing is open until one close beyond it, and a swing confirmed by
    a candle counts only from the next candle on."""

    def __init__(self, doji_max_body: float):
        self._doji = doji_max_body
        self._open: dict[Direction, SwingPoint | None] = dict.fromkeys(Direction)
        self._seen = 0
        self.history: list[Direction] = []

    def update(self, candle: Candle, swings: Sequence[SwingPoint]) -> None:
        """`swings`: all swings confirmed up to and including this candle."""
        for direction, swing in self._open.items():
            if swing is not None and breaks(direction, candle, swing.price, self._doji):
                self._open[direction] = None
                self.history.append(direction)
        for swing in swings[self._seen :]:
            for direction, kind in BROKEN_KIND.items():
                if swing.kind is kind:
                    self._open[direction] = swing
        self._seen = len(swings)


@dataclass(frozen=True, slots=True)
class Signal:
    """A no-wick candle with everything known at its close (no lookahead)."""

    index: int  # candle index in the entry-timeframe series
    direction: Direction
    close_time: datetime
    level: float  # limit price = the candle's open
    wick_share: float
    bos: bool  # last BOS on TF is in the trade direction
    bos_clean: bool  # bos and the last two swing highs / lows both rise (fall for a short)
    bos_4h: bool  # bos and (4h trend agrees or the last two structure breaks agree)
    pdf_skip: bool  # closes in a New York window the `pdf` session variant skips
    swing_stop: float | None = None  # last confirmed swing on the stop side
    prev_swing_stop: float | None = None  # the one before it
    swing_target: float | None = None  # last confirmed swing on the target side
    prev_candle_extreme: float | None = None  # previous candle's low (long) / high (short)
    atr: float | None = None


def scan_signals(
    candles: Sequence[Candle],
    doji_max_body: float,
    h4_candles: Sequence[Candle] = (),
    cfg: StudyConfig | None = None,
    timeframe: Timeframe = Timeframe.M5,
    symbol: str = "STUDY",
) -> list[Signal]:
    """All no-wick candles of `candles` with the structure known at their close: swings
    (confirmed by the signal candle itself counts), BOS, trend, ATR(14) and the 4h trend read
    only from closed 4h candles (`HigherTimeframeClock`). Detectors run incrementally, once
    per closed candle in order, so the result for candle i never depends on later candles."""
    cfg = cfg or StudyConfig()
    series = CandleSeries(symbol, timeframe, candles)
    bos = BosDetector(SwingDetector(doji_max_body))
    atr = Atr(cfg.atr_period)
    tracker = BreakTracker(doji_max_body)
    h4 = Structure(doji_max_body)
    clock = HigherTimeframeClock(CandleSeries(symbol, Timeframe.H4, h4_candles))
    swing_prices: dict[SwingKind, list[float]] = {SwingKind.HIGH: [], SwingKind.LOW: []}
    seen = 0
    out = []
    for i, candle in enumerate(candles):
        view = series.view(i)
        bos.update(view)
        atr.update(view)
        tracker.update(candle, bos.swings)
        for swing in bos.swings[seen:]:
            swing_prices[swing.kind].append(swing.price)
        seen = len(bos.swings)
        found = no_wick_direction(candle, cfg.max_wick_share)
        if found is None:
            continue
        direction, share = found
        close_time = candle.ts + timeframe.duration
        h4.update(clock.view_at(close_time))
        long = direction is Direction.BULLISH
        stop_side = swing_prices[SwingKind.LOW if long else SwingKind.HIGH]
        target_side = swing_prices[SwingKind.HIGH if long else SwingKind.LOW]
        is_bos = bos.trend is direction
        out.append(
            Signal(
                index=i,
                direction=direction,
                close_time=close_time,
                level=candle.open,
                wick_share=share,
                bos=is_bos,
                bos_clean=is_bos
                and clean_structure(
                    direction, swing_prices[SwingKind.HIGH], swing_prices[SwingKind.LOW]
                ),
                bos_4h=is_bos and four_hour_ok(direction, h4.trend, tracker.history),
                pdf_skip=in_pdf_window(close_time, cfg),
                swing_stop=stop_side[-1] if stop_side else None,
                prev_swing_stop=stop_side[-2] if len(stop_side) > 1 else None,
                swing_target=target_side[-1] if target_side else None,
                prev_candle_extreme=(
                    None if i == 0 else (candles[i - 1].low if long else candles[i - 1].high)
                ),
                atr=atr.at(i),
            )
        )
    return out


def stop_prices(sig: Signal, cfg: StudyConfig) -> dict[str, float]:
    """Stop price per variant at the signal's close. A variant whose stop is unknown or not
    beyond the entry (long: not below it) has no trade and is left out. One code path for
    both directions: `sign` is +1 for a long and -1 for a short."""
    sign = 1 if sig.direction is Direction.BULLISH else -1
    entry = sig.level
    out = {}
    for spec in cfg.stops:
        stop = None
        if spec.kind in ("swing", "prevswing"):
            ref = sig.swing_stop if spec.kind == "swing" else sig.prev_swing_stop
            if ref is not None and sign * (entry - ref) > 0:
                stop = ref - spec.value * (entry - ref)  # beyond the swing, away from the entry
        elif spec.kind == "prevcandle":
            stop = sig.prev_candle_extreme
        elif sig.atr is not None:
            stop = entry - sign * spec.value * sig.atr
        if stop is not None and sign * (entry - stop) > 0:
            out[spec.name] = stop
    return out


# --- M1 data, fills and paths ---------------------------------------------------------------------


@dataclass(frozen=True)
class M1Data:
    ts: np.ndarray  # int64 ns UTC, open time of each M1 bar
    open: np.ndarray
    high: np.ndarray
    low: np.ndarray
    close: np.ndarray
    seg_end: np.ndarray  # per bar: index of the last bar before the next data hole


def _m1_data(ts, o, h, low, c, cfg: StudyConfig) -> M1Data:
    ts = np.asarray(ts, dtype="int64")
    hole = np.diff(ts) > int(cfg.gap_hours * 3600 * NS)
    seg_id = np.concatenate([[0], np.cumsum(hole)]) if len(ts) else np.zeros(0, dtype=int)
    ends = np.flatnonzero(np.concatenate([hole, [True]])) if len(ts) else np.zeros(0, dtype=int)
    arrays = [np.asarray(a, dtype=float) for a in (o, h, low, c)]
    return M1Data(ts, *arrays, ends[seg_id])


def m1_from_candles(candles: Sequence[Candle], cfg: StudyConfig) -> M1Data:
    return _m1_data(
        [int(c.ts.timestamp()) * NS for c in candles],
        [c.open for c in candles], [c.high for c in candles],
        [c.low for c in candles], [c.close for c in candles], cfg,
    )  # fmt: skip


def _ns(series: pd.Series) -> np.ndarray:
    """UTC timestamps of a tz-aware pandas column as int64 ns (whatever its unit)."""
    return (
        series.dt.tz_convert("UTC")
        .dt.tz_localize(None)
        .to_numpy()
        .astype("datetime64[ns]")
        .astype("int64")
    )


def m1_from_frame(frame: pd.DataFrame, cfg: StudyConfig) -> M1Data:
    return _m1_data(
        _ns(frame["ts"]), frame["open"], frame["high"], frame["low"], frame["close"], cfg
    )


def find_fill(
    m1: M1Data,
    close: datetime,
    tf: Timeframe,
    level: float,
    direction: Direction,
    cfg: StudyConfig,
) -> tuple[int, float] | None:
    """(M1 index, fill price) of the limit order placed at `close`, or None when it expires.
    The order lives for `expiry_candles` TF candles (M1 bars opening in [close, close + n x
    TF)). The first bar that trades to the level fills at the level; a bar that opens beyond
    it (long: below) fills at its open."""
    lo = int(np.searchsorted(m1.ts, int(close.timestamp()) * NS, side="left"))
    end = close + cfg.expiry_candles * tf.duration
    hi = int(np.searchsorted(m1.ts, int(end.timestamp()) * NS, side="left"))
    if lo >= hi:
        return None
    sign = 1 if direction is Direction.BULLISH else -1
    reach = m1.low[lo:hi] if sign > 0 else m1.high[lo:hi]
    hit = sign * (level - reach) >= 0
    k = int(hit.argmax())
    if not hit[k]:
        return None
    idx = lo + k
    opened = float(m1.open[idx])
    return idx, (opened if sign * (opened - level) < 0 else level)


@lru_cache(maxsize=4096)
def _exit_after(day: date, at: time) -> int:
    return int(datetime.combine(day, at, tzinfo=NY).timestamp()) * NS


def exit_index(m1: M1Data, fill_idx: int, cfg: StudyConfig) -> tuple[int, bool]:
    """(index of the last bar of the trade, filled after the exit time). The trade is closed at
    the close of the last bar opening before 16:55 New York of the fill's day (the next day when
    the fill bar opens at or after 16:55), but no later than the last bar before a data hole."""
    local = datetime.fromtimestamp(int(m1.ts[fill_idx]) // NS, NY)
    late = local.time() >= cfg.exit_time
    day = local.date() + timedelta(days=1 if late else 0)
    by_time = int(np.searchsorted(m1.ts, _exit_after(day, cfg.exit_time), side="left")) - 1
    return min(by_time, int(m1.seg_end[fill_idx])), late


def walk(
    m1: M1Data,
    fill_idx: int,
    end_idx: int,
    fill: float,
    direction: Direction,
    stops: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(stopped, mfe_r, exit_r) per stop price, walking M1 bars fill_idx .. end_idx.

    The fill bar counts for the stop (stop first) but its favourable side does not count; in
    later bars a bar that reaches the stop is the stop bar and its favourable side is not
    counted either. `mfe_r` = best favourable excursion (in R of fill - stop) over the bars
    before the stop bar, or up to the last bar when never stopped (0 when no bar counts);
    `exit_r` = R at the close of the last bar (meaningful when not stopped). Long space:
    a short is mirrored by multiplying prices with -1."""
    sign = 1 if direction is Direction.BULLISH else -1
    seg = slice(fill_idx, end_idx + 1)
    if sign > 0:
        adverse, favourable, last_close = m1.low[seg], m1.high[seg], m1.close[end_idx]
    else:
        adverse, favourable, last_close = -m1.high[seg], -m1.low[seg], -m1.close[end_idx]
    n = len(adverse)
    f = sign * fill
    s = sign * np.asarray(stops, dtype=float)
    risk = f - s
    first_hit = np.searchsorted(-np.minimum.accumulate(adverse), -s, side="left")
    stopped = first_hit < n
    last_counted = np.where(stopped, first_hit - 1, n - 1)
    if n > 1:
        best = np.maximum.accumulate(favourable[1:])
        mfe = np.where(last_counted >= 1, best[np.clip(last_counted - 1, 0, n - 2)] - f, 0.0)
    else:
        mfe = np.zeros(len(s))
    return stopped, mfe / risk, (last_close - f) / risk


def target_outcomes(
    target: float | str,
    mfe_r: np.ndarray,
    stopped: np.ndarray,
    exit_r: np.ndarray,
    swing_target_r: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """(gross R, valid) per record for one target from the walk records, without re-walking.
    Target reached before the stop (MFE >= T) = +T; else stopped = -1; else the time-exit R
    (never more than T). `none`: stop or time exit only. `swing`: T is the row's own swing
    target in R; rows without one (or under the minimum room) are not valid."""
    valid = np.ones(len(mfe_r), dtype=bool)
    if isinstance(target, str) and target == "none":
        return np.where(stopped, -1.0, exit_r), valid
    if isinstance(target, str):
        t = swing_target_r
        valid = ~np.isnan(t)
        t = np.where(valid, t, np.inf)
    else:
        t = np.full(len(mfe_r), float(target))
    with np.errstate(invalid="ignore"):
        reached = mfe_r >= t
    timed = np.minimum(exit_r, t)
    return np.where(reached, t, np.where(stopped, -1.0, timed)), valid


def cost_price(costs: CostConfig, symbol: str, price: float) -> float:
    """Spread + round-turn commission as a price distance, as the engine charges them (the
    spread scaled with the price level when the symbol has a reference price)."""
    return costs.spread(symbol, None, price) + costs.commission_price(symbol, price)


def _bump(counts: dict, key: str, by: int = 1) -> None:
    counts[key] = counts.get(key, 0) + by


def evaluate_signal(
    m1: M1Data,
    sig: Signal,
    tf: Timeframe,
    cfg: StudyConfig,
    costs: CostConfig,
    symbol: str,
    cols: dict[str, list],
    counts: dict[str, int],
) -> None:
    """Fill the signal's limit order on M1 and append one row per surviving stop variant to
    `cols` (a column dict of lists). `counts`: signals / expired / filled / gap_dropped /
    no_stop (stop variants without a valid stop)."""
    _bump(counts, "signals")
    fill = find_fill(m1, sig.close_time, tf, sig.level, sig.direction, cfg)
    if fill is None:
        _bump(counts, "expired")
        return
    _bump(counts, "filled")
    idx, price = fill
    sign = 1 if sig.direction is Direction.BULLISH else -1
    stops = stop_prices(sig, cfg)
    _bump(counts, "no_stop", len(cfg.stops) - len(stops))
    kept = {name: s for name, s in stops.items() if sign * (price - s) > 0}
    _bump(counts, "gap_dropped", len(stops) - len(kept))
    if not kept:
        return
    end, late = exit_index(m1, idx, cfg)
    names = list(kept)
    stop_arr = np.array([kept[n] for n in names])
    stopped, mfe_r, exit_r = walk(m1, idx, end, price, sig.direction, stop_arr)
    risk = sign * (price - stop_arr)
    cprice = cost_price(costs, symbol, price)
    if sig.swing_target is None:
        swing_r = np.full(len(names), math.nan)
    else:
        swing_r = sign * (sig.swing_target - price) / risk
        swing_r = np.where(swing_r >= cfg.min_swing_target_r, swing_r, math.nan)
    k = len(names)
    row = {
        "symbol": [symbol] * k,
        "tf": [tf.name] * k,
        "signal_ns": [int(sig.close_time.timestamp()) * NS] * k,
        "fill_ns": [int(m1.ts[idx])] * k,
        "direction": [sign] * k,
        "wick_share": [sig.wick_share] * k,
        "bos": [sig.bos] * k,
        "bos_clean": [sig.bos_clean] * k,
        "bos_4h": [sig.bos_4h] * k,
        "pdf_skip": [sig.pdf_skip] * k,
        "overnight": [late] * k,
        "stop": names,
        "fill_price": [price] * k,
        "risk": risk.tolist(),
        "mfe_r": mfe_r.tolist(),
        "stopped": stopped.tolist(),
        "exit_r": exit_r.tolist(),
        "cost_price": [cprice] * k,
        "cost_r": (cprice / risk).tolist(),
        "swing_target_r": swing_r.tolist(),
    }
    for name, values in row.items():
        cols.setdefault(name, []).extend(values)


# --- one symbol x timeframe ---------------------------------------------------------------------------


def resample_frame(m1: pd.DataFrame, tf: Timeframe) -> pd.DataFrame:
    """M1 bid OHLC -> `tf` candles (UTC-aligned buckets, as the cache's own resampling)."""
    bucket = m1["ts"].dt.floor(f"{tf.value}min")
    out = m1.groupby(bucket, sort=True).agg(
        open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last")
    )
    return out.rename_axis("ts").reset_index()


def candles_of(frame: pd.DataFrame) -> list[Candle]:
    return [
        Candle(t.to_pydatetime(), o, h, low, c)
        for t, o, h, low, c in zip(
            frame["ts"], frame["open"], frame["high"], frame["low"], frame["close"], strict=True
        )
    ]


def study_frames(
    symbol: str,
    tf: Timeframe,
    m1_frame: pd.DataFrame,
    doji_max_body: float,
    cfg: StudyConfig,
    costs: CostConfig,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """(trades, counts) of one symbol and entry timeframe from an M1 frame with columns ts,
    open, high, low, close (UTC, flat minutes dropped)."""
    candles = candles_of(resample_frame(m1_frame, tf))
    h4 = candles_of(resample_frame(m1_frame, Timeframe.H4))
    signals = scan_signals(candles, doji_max_body, h4, cfg, tf, symbol)
    data = m1_from_frame(m1_frame, cfg)
    cols: dict[str, list] = {}
    counts: dict[str, int] = {}
    for sig in signals:
        evaluate_signal(data, sig, tf, cfg, costs, symbol, cols, counts)
    frame = pd.DataFrame(cols)
    if frame.empty:
        return frame, counts
    for name, source in (("signal_time", "signal_ns"), ("fill_time", "fill_ns")):
        frame[name] = pd.to_datetime(frame.pop(source), unit="ns", utc=True)
    frame["direction"] = frame["direction"].astype("int8")
    return frame, counts


def load_m1(symbol: str, start: date, end: date) -> pd.DataFrame:
    """M1 bid candles of the cached days in [start, end], MT5 preferred day by day."""
    days = [d for d in DEFAULT_SOURCES.cached_days(symbol) if start <= d <= end]
    if not days:
        raise ValueError(f"{symbol}: no cached days between {start} and {end}")
    runs, first, prev = [], days[0], days[0]
    for d in days[1:]:
        if d != prev + timedelta(days=1):
            runs.append((first, prev))
            first = d
        prev = d
    runs.append((first, prev))
    adapter = DEFAULT_SOURCES.adapter(symbol)
    frames = [
        adapter.fetch_frame(
            symbol,
            Timeframe.M1,
            datetime(a.year, a.month, a.day, tzinfo=UTC),
            datetime(b.year, b.month, b.day, tzinfo=UTC) + timedelta(days=1),
        )
        for a, b in runs
    ]
    return pd.concat(frames, ignore_index=True)[["ts", "open", "high", "low", "close"]]


def run_symbol(job: tuple) -> tuple[str, pd.DataFrame | None, list[dict], str | None]:
    """Worker: all timeframes of one symbol (M1 is read once). Returns (symbol, trades, counts
    rows, error). One job per symbol, not per symbol x timeframe, so the M1 files are read once."""
    symbol, tf_names, start, end, cfg = job
    try:
        m1 = load_m1(symbol, start, end)
        doji = DetectorSettings().swings.doji_threshold(symbol)
        costs = CostConfig()
        costs.for_symbol(symbol)  # fail early when the symbol has no cost settings
        frames, rows = [], []
        for name in tf_names:
            trades, counts = study_frames(symbol, Timeframe[name], m1, doji, cfg, costs)
            frames.append(trades)
            rows.append({"symbol": symbol, "tf": name, **counts})
            print(f"{symbol} {name}: {counts.get('signals', 0)} signals, {len(trades)} rows",
                  flush=True)  # fmt: skip
        frames = [f for f in frames if not f.empty]
        return symbol, (pd.concat(frames, ignore_index=True) if frames else None), rows, None
    except Exception as e:  # noqa: BLE001 - research tool: say what is missing, go on
        return symbol, None, [], f"{type(e).__name__}: {e}"


# --- scoring ---------------------------------------------------------------------------------------------


def _label(target: float | str) -> str:
    return target if isinstance(target, str) else f"{target:g}"


def _stats(n, gross, net, net2, wins) -> dict | None:
    """Row of numbers from (symbol, half) aggregates of one variant and group."""
    trades = int(n.sum())
    if trades == 0:
        return None
    mean = net.sum() / trades
    var = (net2.sum() - trades * mean**2) / (trades - 1) if trades > 1 else 0.0
    se = math.sqrt(max(var, 0.0) / trades)
    per_sym = net.sum(axis=1)
    present = n.sum(axis=1) > 0
    half = [net[:, h].sum() / n[:, h].sum() if n[:, h].sum() else math.nan for h in (0, 1)]
    return {
        "trades": trades,
        "win_pct": 100.0 * wins.sum() / trades,
        "gross_r_per_trade": gross.sum() / trades,
        "net_r_per_trade": mean,
        "net_r_total": net.sum(),
        "net_r_per_trade_h1": half[0],
        "net_r_per_trade_h2": half[1],
        "symbols": int(present.sum()),
        "symbols_pos_share": float(((per_sym > 0) & present).sum() / present.sum()),
        "tstat": mean / se if se > 0 else math.nan,
    }


def score_trades(trades: pd.DataFrame, cfg: StudyConfig | None = None) -> pd.DataFrame:
    """Summary per variant (group, tf, trend, session, wick, stop, target): trades, win %,
    gross and net R per trade, net R total, net R per trade in the two halves (fills up to /
    after `first_half_end_year`), share of symbols with net > 0 and the t-stat of net R.
    Groups: ALL and the symbol classes fx / indices / metals / other. Net = gross - cost_r."""
    cfg = cfg or StudyConfig()
    if cfg.max_cost_r is not None:
        trades = trades[trades["cost_r"] <= cfg.max_cost_r]
    if cfg.drop_overnight:
        trades = trades[~trades["overnight"]]
    symbols = sorted(trades["symbol"].unique())
    n_sym = len(symbols)
    sym = pd.Categorical(trades["symbol"], categories=symbols).codes.astype("int64")
    half = (trades["fill_time"].dt.year > cfg.first_half_end_year).to_numpy().astype("int64")
    bits = (
        trades["bos"].to_numpy().astype("int64") * TREND_BITS["bos"]
        + trades["bos_clean"].to_numpy().astype("int64") * TREND_BITS["bos_clean"]
        + trades["bos_4h"].to_numpy().astype("int64") * TREND_BITS["bos_4h"]
    )
    n_w = len(cfg.wick_variants) + 1
    wick_class = np.searchsorted(np.array(cfg.wick_variants), trades["wick_share"].to_numpy())
    pdf = trades["pdf_skip"].to_numpy().astype("int64")
    cell = (bits * n_w + wick_class) * 2 + pdf
    n_cells = 8 * n_w * 2
    key = cell * (2 * n_sym) + sym * 2 + half
    size = n_cells * 2 * n_sym
    cells = np.arange(n_cells)
    cell_bits, cell_wick, cell_pdf = cells // (n_w * 2), (cells // 2) % n_w, cells % 2
    classes = {"ALL": np.ones(n_sym, dtype=bool)}
    for g in ("fx", "indices", "metals", "other"):
        classes[g] = np.array([GROUPS.get(s, "other") == g for s in symbols])
    targets = [*cfg.targets, "swing", "none"]
    rows = []
    for tf in sorted(trades["tf"].unique(), key=lambda x: Timeframe[x].value):
        for spec in cfg.stops:
            pick = ((trades["tf"] == tf) & (trades["stop"] == spec.name)).to_numpy()
            if not pick.any():
                continue
            part = trades[pick]
            k = key[pick]
            for target in targets:
                gross, valid = target_outcomes(
                    target, part["mfe_r"].to_numpy(), part["stopped"].to_numpy(),
                    part["exit_r"].to_numpy(), part["swing_target_r"].to_numpy(),
                )  # fmt: skip
                net = gross - part["cost_r"].to_numpy()
                kv = k[valid]
                agg = [
                    np.bincount(kv, weights=w[valid], minlength=size).reshape(n_cells, n_sym, 2)
                    for w in (np.ones(len(net)), gross, net, net**2, (gross > 0).astype(float))
                ]  # fmt: skip
                for trend, tbit in TREND_BITS.items():
                    in_trend = (cell_bits & tbit) == tbit if tbit else np.ones(n_cells, bool)
                    for session in SESSIONS:
                        for j, wick in enumerate(cfg.wick_variants):
                            sel = in_trend & (cell_wick <= j)
                            if session == "pdf":
                                sel &= cell_pdf == 0
                            sums = [a[sel].sum(axis=0) for a in agg]
                            for group, members in classes.items():
                                if not members.any():
                                    continue
                                stats = _stats(*(s[members] for s in sums))
                                if stats:
                                    rows.append(
                                        {"group": group, "tf": tf, "trend": trend,
                                         "session": session, "wick": wick, "stop": spec.name,
                                         "target": _label(target), **stats}
                                    )  # fmt: skip
    return pd.DataFrame(rows)


def print_report(summary: pd.DataFrame, cfg: StudyConfig) -> None:
    alls = summary[summary["group"] == "ALL"]
    if alls.empty:
        print("no variants with trades")
        return
    top = alls[alls["trades"] >= cfg.min_trades].nlargest(cfg.top, "net_r_per_trade")
    cols = ["tf", "trend", "session", "wick", "stop", "target", "trades", "win_pct",
            "gross_r_per_trade", "net_r_per_trade", "net_r_per_trade_h1", "net_r_per_trade_h2",
            "symbols_pos_share", "tstat"]  # fmt: skip
    print(f"\ntop {cfg.top} variants by net R per trade (ALL symbols, >= {cfg.min_trades} trades)")
    print(top[cols].to_string(index=False, float_format=lambda x: f"{x:.3f}"))
    share = (alls["net_r_per_trade"] > 0).mean()
    print(f"\nshare of variants with net > 0: {share:.1%} of {len(alls)} variants "
          f"({(alls['trades'] >= cfg.min_trades).sum()} with >= {cfg.min_trades} trades)")  # fmt: skip


# --- command line --------------------------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--start", type=date.fromisoformat, default=START)
    p.add_argument("--end", type=date.fromisoformat, default=END)
    p.add_argument("--symbols", nargs="+", default=list(SYMBOLS))
    p.add_argument("--timeframes", nargs="+", choices=[t.name for t in TIMEFRAMES],
                   default=[t.name for t in TIMEFRAMES])  # fmt: skip
    p.add_argument("--workers", type=int, default=1, help="parallel processes (one per symbol)")
    p.add_argument("--out", type=Path, default=None,
                   help="default: results/no_wick_retest/<today>")  # fmt: skip
    p.add_argument("--score", action="store_true",
                   help="recompute summary.csv from <out>/trades.parquet, no data loading")  # fmt: skip
    p.add_argument("--min-trades", type=int, default=StudyConfig().min_trades)
    args = p.parse_args(argv)

    cfg = StudyConfig(min_trades=args.min_trades)
    out = args.out or RESULTS_DIR / "no_wick_retest" / datetime.now(UTC).date().isoformat()
    out.mkdir(parents=True, exist_ok=True)
    if not args.score:
        symbols = [s.upper() for s in args.symbols]
        print(
            "symbols: " + ", ".join(f"{s} (marked)" if s in MARKED_SYMBOLS else s for s in symbols)
        )
        jobs = [(s, tuple(args.timeframes), args.start, args.end, cfg) for s in symbols]
        workers = max(1, min(args.workers, len(jobs), os.cpu_count() or 1))
        if workers == 1:
            results = [run_symbol(j) for j in jobs]
        else:
            with ProcessPoolExecutor(workers) as pool:
                results = list(pool.map(run_symbol, jobs))
        frames, counts = [], []
        for symbol, trades, rows, error in results:
            if error:
                print(f"{symbol}: skipped ({error})")
                continue
            counts += rows
            if trades is not None:
                frames.append(trades)
        if not frames:
            print("no trades")
            return 1
        trades = pd.concat(frames, ignore_index=True)
        for col in ("symbol", "tf", "stop"):
            trades[col] = trades[col].astype("category")
        trades.to_parquet(out / "trades.parquet")
        pd.DataFrame(counts).to_csv(out / "counts.csv", index=False)
        print(f"{len(trades)} rows written to {out / 'trades.parquet'}")
    else:
        trades = pd.read_parquet(out / "trades.parquet")
        for col in ("symbol", "tf", "stop"):
            trades[col] = trades[col].astype(str)
    trades["symbol"] = trades["symbol"].astype(str)
    trades["tf"] = trades["tf"].astype(str)
    trades["stop"] = trades["stop"].astype(str)
    summary = score_trades(trades, cfg)
    summary.to_csv(out / "summary.csv", index=False)
    print_report(summary, cfg)
    print(f"written to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
