"""Entry screening battery: do a strategy's entries carry information, whatever its exit?

Spec: risk-management.md > Entry screening (ROADMAP 12.12, idea T-13; Davey ch.12). The input is
a trade list (entry time = close of the entry bar, direction, entry price, initial stop = 1R) and
the M1 candles of each symbol. The strategy's own exit is replaced by test exits, re-simulated on
M1 with the engine's rules (`engine/trade.py`, `engine/costs.py`):

- a candle opening beyond the stop fills at its open, otherwise at the stop; SL and TP inside one
  candle -> SL first; only candles that open at or after the entry time are used (no lookahead);
- spread on the fills (the entry spread is also paid at the exit), commission, and swap for every
  17:00 New York rollover between the entry time and the exit candle's close time.

Test exits: (a) close of bar N of the signal timeframe after the entry, own stop active;
(b) 1R / 1R bracket; (c) random exit time, mean hold matched, own stop active; (d) the reversed
signal for each of them (opposite direction, stop mirrored at the same distance, costs paid
again); (e) the share of entries that are in the money N bars later, against the same scan on
shuffled entry times.

Choices the spec leaves open (documented, ROADMAP 12.12):
- "N bars later" is the last M1 candle that closed by entry time + N x bar minutes, but never
  before the first candle after the entry (a data gap or the weekend therefore ends the hold at
  the last candle before the gap, or at the first one after it when there is none in between).
- Random exit: the hold is drawn uniform on [0, 2 x mean hold] seconds per trade and run, so the
  mean hold is the strategy's mean hold in expectation (sample mean reported). The percentile is
  that of the strategy's own total net R among the random runs' totals (ties count half).
- Trading window of the shuffled scan: the New York weekdays and the `window_bucket_minutes`
  time-of-day buckets in which the strategy entered (per symbol), within the entry date range;
  a shuffled entry is a uniformly drawn M1 candle close inside that window, with the direction
  of the real trade it replaces.
- 1R / 1R win rate = target hits / (target + stop hits); trades unresolved at the end of the
  data are left out.
- Pass rule across several variants: cells and bracket results pooled, percentile = median.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta

import numpy as np
import pandas as pd

from backtester.analytics.verdict import middle_date
from backtester.core.models import Direction
from backtester.engine.costs import CostConfig
from backtester.sessions import ROLLOVER_TIME, ROLLOVER_ZONE

SECONDS_PER_MINUTE = 60
ROLLOVER_WEEKDAYS = range(5)  # same as engine/costs.py
SCAN_CHUNK = 1024  # candles per vectorised stop / target scan (doubles while nothing is hit)
TIE_TOLERANCE = 1e-12
PERCENT = 100.0
MIN_HOLD_S = float(SECONDS_PER_MINUTE)


@dataclass(frozen=True, slots=True)
class EntryScreenConfig:
    bars: tuple[int, ...] = (1, 2, 3, 5, 10, 20)  # spec: N set
    bracket_r: float = 1.0  # spec: stop and target one R from the entry
    random_runs: int = 1000  # spec: 1,000 seeded runs
    shuffle_runs: int = 1000  # spec: 1,000 shuffled entry-time scans
    seed: int = 42  # spec: every random draw seeded with 42
    min_cell_share: float = 0.70  # spec: mean net R > 0 in >= 70 % of the cells
    min_bracket_win_rate: float = 0.52  # spec: 1R / 1R win rate >= 52 %
    random_percentile: float = 90.0  # spec: strategy above the 90th percentile of random exits
    window_bucket_minutes: int = 15  # time-of-day resolution of the shuffled-entry window

    def __post_init__(self) -> None:
        if not self.bars or any(n < 1 for n in self.bars):
            raise ValueError("bars must be a non-empty set of N >= 1")
        if self.bracket_r <= 0:
            raise ValueError("bracket_r must be > 0")
        if self.random_runs < 1 or self.shuffle_runs < 1:
            raise ValueError("runs must be >= 1")
        if self.window_bucket_minutes < 1:
            raise ValueError("window_bucket_minutes must be >= 1")


# --- inputs -----------------------------------------------------------------------------------------


@dataclass(frozen=True)
class M1Data:
    """M1 candles of one symbol as arrays; `open_s` = candle open time, epoch seconds UTC."""

    open_s: np.ndarray
    open: np.ndarray
    high: np.ndarray
    low: np.ndarray
    close: np.ndarray

    @property
    def close_s(self) -> np.ndarray:
        return self.open_s + SECONDS_PER_MINUTE

    def __len__(self) -> int:
        return len(self.open_s)

    @classmethod
    def from_candles(cls, candles: Sequence) -> M1Data:
        return cls(
            np.array([int(c.ts.timestamp()) for c in candles], dtype=np.int64),
            np.array([c.open for c in candles], dtype=float),
            np.array([c.high for c in candles], dtype=float),
            np.array([c.low for c in candles], dtype=float),
            np.array([c.close for c in candles], dtype=float),
        )

    @classmethod
    def from_frame(cls, frame: pd.DataFrame) -> M1Data:
        """From a cache frame (columns ts, open, high, low, close), sorted by ts."""
        ts = frame["ts"].dt.tz_convert("UTC").dt.tz_localize(None).to_numpy()
        return cls(
            ts.astype("datetime64[s]").astype(np.int64),
            frame["open"].to_numpy(float),
            frame["high"].to_numpy(float),
            frame["low"].to_numpy(float),
            frame["close"].to_numpy(float),
        )


@dataclass(frozen=True, slots=True)
class ScreenTrade:
    """What the battery needs of a backtest trade."""

    symbol: str
    direction: Direction
    entry_time: datetime  # close time of the entry bar (aware)
    entry: float  # chart (bid) price
    initial_stop: float
    exit_time: datetime  # the strategy's own exit (mean hold)
    r_net: float  # the strategy's own net R

    @property
    def risk(self) -> float:
        return abs(self.entry - self.initial_stop)

    @property
    def sign(self) -> int:
        return 1 if self.direction is Direction.BULLISH else -1

    @classmethod
    def from_trade(cls, t) -> ScreenTrade:
        return cls(
            t.symbol, t.direction, t.entry_time, t.entry, t.initial_stop, t.exit_time, t.r_net
        )


@dataclass(frozen=True, slots=True)
class ExitResult:
    exit_time: datetime  # close time of the exit candle
    exit_price: float  # chart (bid) price
    reason: str  # stop | target | time | end_of_data
    r_gross: float
    r_net: float
    swap_r: float


# --- rollover / swap -------------------------------------------------------------------------------


def rollover_schedule(
    entry_time: datetime, last_time: datetime, triple_weekday: int
) -> tuple[np.ndarray, np.ndarray]:
    """(epoch seconds of the 17:00 New York rollovers with entry_time < rollover <= last_time,
    cumulative nights counted like `engine/costs.py rollover_nights`: 3 on the triple weekday)."""
    first = entry_time.astimezone(ROLLOVER_ZONE).date()
    last = last_time.astimezone(ROLLOVER_ZONE).date()
    times, nights, day = [], [], first
    while day <= last:
        if day.weekday() in ROLLOVER_WEEKDAYS:
            at = datetime.combine(day, ROLLOVER_TIME, ROLLOVER_ZONE)
            if entry_time < at <= last_time:
                times.append(at.timestamp())
                nights.append(3 if day.weekday() == triple_weekday else 1)
        day += timedelta(days=1)
    return np.array(times, dtype=float), np.cumsum(np.array(nights, dtype=np.int64))


# --- the exit simulation (one leg: a direction, an entry, a stop) ----------------------------------


def _entry_index(m1: M1Data, trade: ScreenTrade) -> int:
    """First candle that opens at or after the entry time (the entry bar itself is closed)."""
    return int(np.searchsorted(m1.open_s, int(trade.entry_time.timestamp()), side="left"))


def _scan(
    m1: M1Data, i0: int, i1: int, sign: int, stop: float, target: float | None = None
) -> tuple[int | None, str | None]:
    """First candle in [i0, i1] that hits the stop or the target; stop first inside one candle."""
    pos, size = i0, SCAN_CHUNK
    while pos <= i1:
        end = min(pos + size, i1 + 1)
        lo, hi = m1.low[pos:end], m1.high[pos:end]
        worst, best = (lo, hi) if sign > 0 else (hi, lo)
        hit_stop = sign * (worst - stop) <= 0
        hit = hit_stop
        if target is not None:
            hit = hit_stop | (sign * (best - target) >= 0)
        if hit.any():
            k = int(np.argmax(hit))
            return pos + k, ("stop" if hit_stop[k] else "target")
        pos, size = end, size * 2
    return None, None


def _stop_fill(m1: M1Data, idx: int, sign: int, stop: float) -> float:
    """Engine rule: a candle that opens beyond the stop fills at its open, else at the stop."""
    return stop if sign * (m1.open[idx] - stop) >= 0 else float(m1.open[idx])


def _leg(trade: ScreenTrade, reverse: bool) -> tuple[int, float]:
    """(sign, stop) of the leg: the reversed one trades the other way with the stop mirrored."""
    sign = -trade.sign if reverse else trade.sign
    return sign, trade.entry - sign * trade.risk


def _direction(sign: int) -> Direction:
    return Direction.BULLISH if sign > 0 else Direction.BEARISH


def _costed(
    costs: CostConfig, trade: ScreenTrade, sign: int, price: float, exit_time: datetime,
    reason: str,
) -> ExitResult:  # fmt: skip
    """Gross and net R of a leg that exits at chart price `price` (engine formulas)."""
    risk, entry, symbol = trade.risk, trade.entry, trade.symbol
    spread = costs.spread(symbol, trade.entry_time, entry)
    fill = price if sign > 0 else price + spread
    entry_fill = entry + spread if sign > 0 else entry
    direction = _direction(sign)
    commission = costs.commission_r(symbol, risk, entry, [(1.0, fill)])
    swap = costs.swap_r(symbol, direction, risk, trade.entry_time, [(1.0, exit_time)], entry)
    funding = costs.funding_r(symbol, direction, risk, trade.entry_time, [(1.0, exit_time)], entry)
    net = sign * (fill - entry_fill) / risk - commission + swap + funding
    return ExitResult(exit_time, price, reason, sign * (price - entry) / risk, net, swap)


def _close_dt(m1: M1Data, idx: int) -> datetime:
    return datetime.fromtimestamp(int(m1.close_s[idx]), tz=UTC)


def _last_closed_by(m1: M1Data, deadline_s: float, i0: int) -> int:
    idx = int(np.searchsorted(m1.close_s, deadline_s, side="right")) - 1
    return max(idx, i0)


def exit_after_bars(
    m1: M1Data, trade: ScreenTrade, bars: int, bar_minutes: int, costs: CostConfig,
    reverse: bool = False,
) -> ExitResult | None:  # fmt: skip
    """(a) Exit at the close of bar `bars` of `bar_minutes` minutes after the entry, the stop
    active. None when no candle follows the entry."""
    i0 = _entry_index(m1, trade)
    if i0 >= len(m1) or trade.risk <= 0:
        return None
    sign, stop = _leg(trade, reverse)
    deadline = int(trade.entry_time.timestamp()) + bars * bar_minutes * SECONDS_PER_MINUTE
    i_end = _last_closed_by(m1, deadline, i0)
    idx, _ = _scan(m1, i0, i_end, sign, stop)
    if idx is not None:
        return _costed(
            costs, trade, sign, _stop_fill(m1, idx, sign, stop), _close_dt(m1, idx), "stop"
        )
    return _costed(costs, trade, sign, float(m1.close[i_end]), _close_dt(m1, i_end), "time")


def exit_bracket(
    m1: M1Data, trade: ScreenTrade, costs: CostConfig, r: float = 1.0, reverse: bool = False
) -> ExitResult | None:
    """(b) Stop one R and target `r` R from the entry (the reversed leg swaps the sides); runs to
    the end of the data when neither is hit (`end_of_data`)."""
    i0 = _entry_index(m1, trade)
    if i0 >= len(m1) or trade.risk <= 0:
        return None
    sign, stop = _leg(trade, reverse)
    target = trade.entry + sign * r * trade.risk
    idx, kind = _scan(m1, i0, len(m1) - 1, sign, stop, target)
    if idx is None:
        last = len(m1) - 1
        return _costed(
            costs, trade, sign, float(m1.close[last]), _close_dt(m1, last), "end_of_data"
        )
    if kind == "stop":
        return _costed(
            costs, trade, sign, _stop_fill(m1, idx, sign, stop), _close_dt(m1, idx), "stop"
        )
    return _costed(costs, trade, sign, target, _close_dt(m1, idx), "target")


# --- (c) random exit time -------------------------------------------------------------------------


@dataclass(frozen=True)
class RandomRuns:
    gross: np.ndarray  # R per hold
    net: np.ndarray


def random_exit_runs(
    m1: M1Data, trade: ScreenTrade, hold_s: np.ndarray, costs: CostConfig, reverse: bool = False
) -> RandomRuns | None:
    """The trade exited after each hold in `hold_s` seconds (the last candle closed by then),
    the stop active; vectorised, equal to `exit_after_bars` for the same exit candle."""
    i0 = _entry_index(m1, trade)
    if i0 >= len(m1) or trade.risk <= 0:
        return None
    sign, stop = _leg(trade, reverse)
    risk, entry, symbol = trade.risk, trade.entry, trade.symbol
    if costs.funding_series(symbol) is not None:
        raise NotImplementedError("random exits with Binance funding are not supported")
    entry_s = int(trade.entry_time.timestamp())
    deadlines = entry_s + np.asarray(hold_s, dtype=float)
    ends = np.maximum(np.searchsorted(m1.close_s, deadlines, side="right") - 1, i0)
    i_h = int(ends.max())
    stop_idx, _ = _scan(m1, i0, i_h, sign, stop)
    stopped = np.zeros(len(ends), dtype=bool) if stop_idx is None else stop_idx <= ends
    price = m1.close[ends]
    exit_s = m1.close_s[ends].astype(float)
    if stop_idx is not None:
        price = np.where(stopped, _stop_fill(m1, stop_idx, sign, stop), price)
        exit_s = np.where(stopped, float(m1.close_s[stop_idx]), exit_s)
    spread = costs.spread(symbol, trade.entry_time, entry)
    fill = price if sign > 0 else price + spread
    entry_fill = entry + spread if sign > 0 else entry
    gross = sign * (price - entry) / risk
    # commission in R is linear in the exit fill (percentage commission): read it at 0 and 1
    base = costs.commission_r(symbol, risk, entry, [(1.0, 0.0)])
    slope = costs.commission_r(symbol, risk, entry, [(1.0, 1.0)]) - base
    commission = base + slope * fill
    times, cum = rollover_schedule(
        trade.entry_time, datetime.fromtimestamp(float(exit_s.max()), tz=UTC),
        costs.for_symbol(symbol).swap_triple_weekday,
    )  # fmt: skip
    k = np.searchsorted(times, exit_s, side="right")
    nights = np.where(k > 0, cum[np.maximum(k - 1, 0)] if len(cum) else 0, 0)
    per_night = costs.swap_r_nights(symbol, _direction(sign), risk, 1.0, entry)
    net = sign * (fill - entry_fill) / risk - commission + nights * per_night
    return RandomRuns(gross, net)


# --- (e) hit-rate scan ----------------------------------------------------------------------------


def _hit_signs(m1: M1Data, refs: np.ndarray, ref_price: np.ndarray, bars: int, bar_minutes: int):
    """Sign (-1, 0, +1) of the price `bars` bars after each reference candle, vs its close."""
    later = (
        np.searchsorted(m1.close_s, m1.close_s[refs] + bars * bar_minutes * 60, side="right") - 1
    )
    later = np.maximum(later, refs + 1)
    ok = later < len(m1)
    out = np.zeros(len(refs), dtype=np.int8)
    out[ok] = np.sign(m1.close[later[ok]] - ref_price[ok]).astype(np.int8)
    return out


def _window_candidates(
    m1: M1Data, entry_times: Sequence[datetime], bucket_minutes: int
) -> np.ndarray:
    """Candle indices whose close lies in the strategy's trading window (see module doc)."""
    zone = ROLLOVER_ZONE
    local = [t.astimezone(zone) for t in entry_times]
    buckets = {(t.hour * 60 + t.minute) // bucket_minutes for t in local}
    weekdays = {t.weekday() for t in local}
    lo = datetime.combine(
        min(t.astimezone(UTC).date() for t in entry_times), datetime.min.time(), UTC
    )
    hi = datetime.combine(max(t.astimezone(UTC).date() for t in entry_times) + timedelta(days=1),
                          datetime.min.time(), UTC)  # fmt: skip
    in_range = (m1.close_s >= lo.timestamp()) & (m1.close_s < hi.timestamp())
    stamp = pd.to_datetime(m1.close_s[in_range], unit="s", utc=True).tz_convert(zone)
    minute_of_day = stamp.hour * 60 + stamp.minute
    ok = np.isin(minute_of_day // bucket_minutes, list(buckets)) & np.isin(
        stamp.dayofweek, list(weekdays)
    )
    return np.flatnonzero(in_range)[np.asarray(ok)]


# --- the screen of one variant --------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class RandomSummary:
    mean_hold_s: float  # the strategy's mean hold
    sample_mean_hold_s: float  # mean of the drawn holds
    runs: int
    strategy_net: float  # the strategy's own total net R (same trades)
    median: float
    p5: float
    p95: float
    percentile: float  # of the strategy's total among the runs
    rev_median: float  # reversed signal with the same random exits
    rev_p5: float
    rev_p95: float


@dataclass(frozen=True)
class VariantScreen:
    label: str
    trades: int  # screened
    skipped: int  # no candle after the entry
    cells: list[dict]
    bracket: dict
    random: RandomSummary
    hit_rows: list[dict]
    n_trades_by_symbol: dict[str, int] = field(default_factory=dict)


def _mean(values) -> float | None:
    return float(np.mean(values)) if len(values) else None


def _cell_row(bars: int, trades, orig, rev, middle: date) -> dict:
    gross = np.array([x.r_gross for x in orig])
    net = np.array([x.r_net for x in orig])
    rgross = np.array([x.r_gross for x in rev])
    rnet = np.array([x.r_net for x in rev])
    long = np.array([t.sign > 0 for t in trades], dtype=bool)
    first = np.array([t.entry_time.date() <= middle for t in trades], dtype=bool)
    return {
        "bars": bars, "trades": len(trades),
        "win_rate": _mean(net > 0), "mean_gross": _mean(gross), "mean_net": _mean(net),
        "long_trades": int(long.sum()), "long_mean_net": _mean(net[long]),
        "short_trades": int((~long).sum()), "short_mean_net": _mean(net[~long]),
        "first_half_trades": int(first.sum()), "first_half_mean_net": _mean(net[first]),
        "second_half_trades": int((~first).sum()), "second_half_mean_net": _mean(net[~first]),
        "rev_win_rate": _mean(rnet > 0), "rev_mean_gross": _mean(rgross),
        "rev_mean_net": _mean(rnet),
    }  # fmt: skip


def _bracket_summary(orig, rev, trades) -> dict:
    def stats(results):
        wins = sum(r.reason == "target" for r in results)
        losses = sum(r.reason == "stop" for r in results)
        return wins, losses, len(results) - wins - losses

    wins, losses, open_ = stats(orig)
    rwins, rlosses, _ = stats(rev)
    resolved = wins + losses
    return {
        "trades": len(trades), "wins": wins, "losses": losses, "unresolved": open_,
        "win_rate": wins / resolved if resolved else 0.0,
        "mean_gross": _mean([r.r_gross for r in orig]), "mean_net": _mean([r.r_net for r in orig]),
        "rev_wins": rwins, "rev_losses": rlosses,
        "rev_win_rate": rwins / (rwins + rlosses) if rwins + rlosses else 0.0,
        "rev_mean_net": _mean([r.r_net for r in rev]),
    }  # fmt: skip


def _percentile_of(value: float, runs: np.ndarray) -> float:
    below = np.sum(runs < value - TIE_TOLERANCE)
    ties = np.sum(np.abs(runs - value) <= TIE_TOLERANCE)
    return PERCENT * float(below + 0.5 * ties) / len(runs)


def screen_variant(
    trades: Sequence[ScreenTrade], m1s: Mapping[str, M1Data], bar_minutes: int,
    costs: CostConfig, config: EntryScreenConfig | None = None, label: str = "default",
    period: tuple[date, date] | None = None,
) -> VariantScreen:  # fmt: skip
    """Run the battery on one variant's trades (see the module docstring)."""
    cfg = config or EntryScreenConfig()
    usable, skipped = [], 0
    for t in trades:
        m1 = m1s.get(t.symbol)
        if m1 is None or _entry_index(m1, t) >= len(m1) or t.risk <= 0:
            skipped += 1
        else:
            usable.append(t)
    if period is None and usable:
        dates = [t.entry_time.date() for t in usable]
        period = (min(dates), max(dates))
    middle = middle_date(*period) if period else date.min
    # (a) + (d)
    cells = []
    for n in cfg.bars:
        orig = [exit_after_bars(m1s[t.symbol], t, n, bar_minutes, costs) for t in usable]
        rev = [exit_after_bars(m1s[t.symbol], t, n, bar_minutes, costs, True) for t in usable]
        cells.append(_cell_row(n, usable, orig, rev, middle))
    # (b)
    b_orig = [exit_bracket(m1s[t.symbol], t, costs, cfg.bracket_r) for t in usable]
    b_rev = [exit_bracket(m1s[t.symbol], t, costs, cfg.bracket_r, True) for t in usable]
    bracket = _bracket_summary(b_orig, b_rev, usable)
    # (c)
    random = _random_summary(usable, m1s, costs, cfg)
    hit_rows = _hit_scan(usable, m1s, bar_minutes, cfg)
    by_symbol: dict[str, int] = {}
    for t in usable:
        by_symbol[t.symbol] = by_symbol.get(t.symbol, 0) + 1
    return VariantScreen(label, len(usable), skipped, cells, bracket, random, hit_rows, by_symbol)


def _random_summary(usable, m1s, costs, cfg: EntryScreenConfig) -> RandomSummary:
    if not usable:
        nan = float("nan")
        return RandomSummary(0.0, 0.0, cfg.random_runs, 0.0, nan, nan, nan, nan, nan, nan, nan)
    mean_hold = max(
        float(np.mean([(t.exit_time - t.entry_time).total_seconds() for t in usable])), MIN_HOLD_S
    )
    rng = np.random.default_rng([cfg.seed, 0])
    totals = np.zeros(cfg.random_runs)
    rev_totals = np.zeros(cfg.random_runs)
    hold_sum = 0.0
    for t in usable:
        holds = rng.uniform(0.0, 2.0 * mean_hold, cfg.random_runs)
        hold_sum += float(holds.sum())
        totals += random_exit_runs(m1s[t.symbol], t, holds, costs).net
        rev_totals += random_exit_runs(m1s[t.symbol], t, holds, costs, True).net
    strategy = float(sum(t.r_net for t in usable))
    p5, p50, p95 = np.percentile(totals, [5, 50, 95])
    r5, r50, r95 = np.percentile(rev_totals, [5, 50, 95])
    return RandomSummary(
        mean_hold, hold_sum / (cfg.random_runs * len(usable)), cfg.random_runs, strategy,
        float(p50), float(p5), float(p95), _percentile_of(strategy, totals),
        float(r50), float(r5), float(r95),
    )  # fmt: skip


def _hit_scan(usable, m1s, bar_minutes: int, cfg: EntryScreenConfig) -> list[dict]:
    n_bars = len(cfg.bars)
    if not usable:
        return []
    real_hits = np.zeros(n_bars)
    by_symbol: dict[str, list[ScreenTrade]] = {}
    for t in usable:
        by_symbol.setdefault(t.symbol, []).append(t)
    shuffles: list[tuple[np.ndarray, np.ndarray, np.ndarray]] = []  # (up signs, sign, n)
    for symbol, ts in by_symbol.items():
        m1 = m1s[symbol]
        signs = np.array([t.sign for t in ts])
        refs = np.array([_entry_index(m1, t) - 1 for t in ts])
        refs = np.maximum(refs, 0)
        entry = np.array([t.entry for t in ts])
        for j, n in enumerate(cfg.bars):
            real_hits[j] += np.sum(_hit_signs(m1, refs, entry, n, bar_minutes) == signs)
        cand = _window_candidates(m1, [t.entry_time for t in ts], cfg.window_bucket_minutes)
        if len(cand) == 0:
            continue
        up = np.stack(
            [_hit_signs(m1, cand, m1.close[cand], n, bar_minutes) for n in cfg.bars], axis=1
        )
        shuffles.append((up, signs, len(ts)))
    total = len(usable)
    rng = np.random.default_rng([cfg.seed, 1])
    sim = np.zeros((cfg.shuffle_runs, n_bars))
    for r in range(cfg.shuffle_runs):
        for up, signs, _n in shuffles:
            draws = rng.integers(0, len(up), len(signs))
            sim[r] += (up[draws] == signs[:, None]).sum(axis=0)
    sim /= total
    rows = []
    for j, n in enumerate(cfg.bars):
        real = real_hits[j] / total
        mean, sd = float(sim[:, j].mean()), float(sim[:, j].std())
        rows.append(
            {
                "bars": n, "trades": total, "real_hit_rate": float(real),
                "shuffled_mean": mean, "shuffled_sd": sd,
                "z": (real - mean) / sd if sd > 0 else 0.0,
                "percentile": _percentile_of(real, sim[:, j]),
            }
        )  # fmt: skip
    return rows


# --- the verdict -------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Verdict:
    passed: bool
    reasons: tuple[str, ...]
    cells: int
    cells_positive: int
    cell_share: float
    bracket_win_rate: float
    random_percentile: float


def passes(
    cell_share: float, win_rate: float, percentile: float, config: EntryScreenConfig
) -> tuple[bool, list[str]]:
    """The spec's pass rule; the reasons list every failed part."""
    why = []
    if cell_share < config.min_cell_share - TIE_TOLERANCE:
        why.append(
            f"mean net R > 0 in {cell_share:.1%} of the cells (needs >= {config.min_cell_share:.0%})"
        )
    if win_rate < config.min_bracket_win_rate - TIE_TOLERANCE:
        why.append(f"1R/1R win rate {win_rate:.1%} (needs >= {config.min_bracket_win_rate:.0%})")
    if not percentile > config.random_percentile:
        why.append(
            f"percentile vs random-time exits {percentile:.1f} (needs > {config.random_percentile:g})"
        )
    return not why, why


def judge(variants: Sequence[VariantScreen], config: EntryScreenConfig | None = None) -> Verdict:
    """Pass / fail over the screened variants: cells pooled, bracket trades pooled, percentile =
    median of the variants'."""
    cfg = config or EntryScreenConfig()
    cells = [c for v in variants for c in v.cells]
    positive = sum(1 for c in cells if c["mean_net"] is not None and c["mean_net"] > 0)
    share = positive / len(cells) if cells else 0.0
    wins = sum(v.bracket["wins"] for v in variants)
    resolved = wins + sum(v.bracket["losses"] for v in variants)
    win_rate = wins / resolved if resolved else 0.0
    pcts = [v.random.percentile for v in variants if v.trades]
    percentile = float(np.median(pcts)) if pcts else 0.0
    ok, why = passes(share, win_rate, percentile, cfg)
    return Verdict(ok, tuple(why), len(cells), positive, share, win_rate, percentile)
