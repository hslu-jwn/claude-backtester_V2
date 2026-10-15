"""Open / gap / trend-day study on index CFDs (NAS100, US500). Spec: ROADMAP.md › 11.2;
knowledge base I-09, I-39 (Hougaard, Aziz, Kaufman ch.15-16). Pure functions, no pandas.

A *cash day* is the M1 bars whose New York time is in [09:30, 16:00); an M1 bar with open time
t closes at t + 1 minute and "known at T" means bars opening before T. Days are classified
(`regular`, `early_close`, `first_bar_missing`, `data_hole`) so holidays, half days and the
data holes of the cache are left out and counted instead of being guessed.

`day_records` turns the regular days into one flat record each. Some fields are *features*
(known by 11:00: the gap, the first 30 minutes, whether the gap is filled by 11:00, ...), the
others are *outcomes* of the day (fill, trend day, timing of the extremes, last hour); a
feature never reads a bar that was not closed at its time, and `FEATURE_FIELDS` lists them so
a test can prove it. `filled_by_day3` looks into the next days on purpose: it is an outcome.

`summarize_*` give the tables by half (and bucket); `wilson`, `arcsine_share`, `mean_t` are
the small statistics next to them.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from itertools import pairwise
from typing import NamedTuple
from zoneinfo import ZoneInfo

from backtester.analytics.metrics import WEEKDAY_NAMES, month_part
from backtester.analytics.robustness import RobustnessConfig

REGULAR = "regular"
EARLY_CLOSE = "early_close"
FIRST_BAR_MISSING = "first_bar_missing"
DATA_HOLE = "data_hole"
MAX_BUCKET_LABEL = "1+"
TREND_UP, TREND_DOWN, TREND_NONE = "up", "down", "none"
EVENT_HIGH, EVENT_LOW, EVENT_BOTH, EVENT_NONE = "high", "low", "both", "none"

# fields known by the feature time (11:00): the study's candidate rule inputs
FEATURE_FIELDS = (
    "date", "year", "half", "weekday", "month_part", "open", "prev_close", "skipped_days",
    "atr", "gap", "gap_atr", "gap_dir", "gap_bucket", "flat", "first30_atr",
    "filled_by_11", "new_extreme_10_11", "pos_11",
)  # fmt: skip


@dataclass(frozen=True, slots=True)
class OpenGapConfig:
    zone: str = "America/New_York"
    cash_open: time = time(9, 30)
    cash_close: time = time(16, 0)
    first_window_end: time = time(10, 0)  # first 30 minutes
    feature_time: time = time(11, 0)  # features are known at this time
    extreme_window_min: int = 90  # "first 90 minutes" of the day
    first_hour_min: int = 60
    last_hour_start: time = time(15, 0)
    atr_period: int = 14  # daily ATR over regular cash days
    max_missing_bars: int = 5  # a regular day may miss this many M1 bars
    min_gap_atr: float = 0.02  # smaller gaps are "flat"
    gap_buckets: tuple[float, ...] = (0.1, 0.25, 0.5, 1.0)  # in daily ATR
    trend_extreme_frac: float = 0.10  # open / close within this share of the range's end
    pos_extreme_frac: float = 0.20  # "close at 11:00 in the extreme fifth of the range so far"
    fill_horizon_days: int = 3  # the day itself and the next regular days
    first_half_end_year: int = RobustnessConfig().first_half_end_year
    half_labels: tuple[str, str] = ("2020-22", "2023-26")

    def __post_init__(self) -> None:
        if self.atr_period < 1:
            raise ValueError("atr_period must be >= 1")
        if self.fill_horizon_days < 1:
            raise ValueError("fill_horizon_days must be >= 1")
        if not 0 < self.trend_extreme_frac <= 0.5:
            raise ValueError("trend_extreme_frac must be in (0, 0.5]")
        if not 0 < self.pos_extreme_frac <= 0.5:
            raise ValueError("pos_extreme_frac must be in (0, 0.5]")
        b = self.gap_buckets
        if not b or b[0] <= 0 or any(x >= y for x, y in pairwise(b)):
            raise ValueError("gap_buckets must be positive and strictly increasing")
        if self.max_missing_bars < 0:
            raise ValueError("max_missing_bars must be >= 0")

    @property
    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.zone)

    def minute_of(self, t: time) -> int:
        """Minutes from the cash open to the clock time `t`."""
        return t.hour * 60 + t.minute - (self.cash_open.hour * 60 + self.cash_open.minute)

    @property
    def session_minutes(self) -> int:
        return self.minute_of(self.cash_close)

    def bucket_labels(self) -> list[str]:
        edges = (0.0, *self.gap_buckets)
        labels = [f"<{edges[1]:g}"]
        labels += [f"{a:g}-{b:g}" for a, b in pairwise(self.gap_buckets)]
        return [*labels, f"{self.gap_buckets[-1]:g}+"]

    def bucket(self, gap_atr: float) -> str:
        labels = self.bucket_labels()
        for edge, label in zip(self.gap_buckets, labels, strict=False):
            if gap_atr < edge:
                return label
        return labels[-1]

    def half(self, year: int) -> str:
        return self.half_labels[0] if year <= self.first_half_end_year else self.half_labels[1]


class Bar(NamedTuple):
    ts: datetime  # open time, UTC
    open: float
    high: float
    low: float
    close: float


@dataclass(frozen=True)
class CashDay:
    date: date  # New York date
    cls: str
    bars: tuple[Bar, ...]  # the cash-hour bars in time order
    minutes: tuple[int, ...]  # minute of each bar after the cash open


def cash_days(bars: Iterable[Bar], cfg: OpenGapConfig | None = None) -> list[CashDay]:
    """The cash-hour bars grouped by New York date, in date order, each day classified.
    `regular`: the 09:30 and the last (15:59) bar exist and at most `max_missing_bars` are
    missing; `early_close`: no last bar but no hole either (holiday CFD sessions, half days);
    `first_bar_missing`; otherwise `data_hole`. Weekdays without any cash bar do not appear."""
    cfg = cfg or OpenGapConfig()
    tz, last = cfg.tz, cfg.session_minutes - 1
    groups: dict[date, list[tuple[int, Bar]]] = {}
    for b in sorted(bars, key=lambda x: x.ts):
        local = b.ts.astimezone(tz)
        m = cfg.minute_of(local.time())
        if 0 <= m <= last:
            groups.setdefault(local.date(), []).append((m, b))
    days = []
    for d in sorted(groups):
        items = groups[d]
        minutes = tuple(m for m, _ in items)
        have_first, have_last = minutes[0] == 0, minutes[-1] == last
        missing = cfg.session_minutes - len(items)
        holes = (minutes[-1] + 1) - len(items)
        if not have_first:
            cls = FIRST_BAR_MISSING
        elif have_last and missing <= cfg.max_missing_bars:
            cls = REGULAR
        elif not have_last and holes <= cfg.max_missing_bars:
            cls = EARLY_CLOSE
        else:
            cls = DATA_HOLE
        days.append(CashDay(d, cls, tuple(b for _, b in items), minutes))
    return days


def known_at(day: CashDay, at: time, cfg: OpenGapConfig | None = None) -> tuple[Bar, ...]:
    """The bars of the day that opened before the clock time `at` (closed by `at`)."""
    cfg = cfg or OpenGapConfig()
    limit = cfg.minute_of(at)
    return tuple(b for b, m in zip(day.bars, day.minutes, strict=True) if m < limit)


# --- ATR and the records of the regular days ------------------------------------------------------


def _atr_before(regular: Sequence[CashDay], period: int) -> list[float | None]:
    """Daily Wilder ATR over regular days, the value known BEFORE each of them (after the
    previous days): None for the first `period` days."""
    out: list[float | None] = []
    atr: float | None = None
    trs: list[float] = []
    prev_close: float | None = None
    for day in regular:
        out.append(atr)
        high = max(b.high for b in day.bars)
        low = min(b.low for b in day.bars)
        tr = high - low
        if prev_close is not None:
            tr = max(tr, abs(high - prev_close), abs(low - prev_close))
        prev_close = day.bars[-1].close
        if atr is None:
            trs.append(tr)
            if len(trs) == period:
                atr = sum(trs) / period
        else:
            atr = (atr * (period - 1) + tr) / period
    return out


def _first_of_two(bars: Sequence[Bar], fill: float, extend: float, up_gap: bool) -> str:
    """Which of the two levels the day trades at first: "fill" (the previous close),
    "extend" (the same distance on the other side of the open), "same_bar" (both inside
    one M1 bar, order unknown: a stop would be assumed hit first) or "neither"."""
    for b in bars:
        f = b.low <= fill if up_gap else b.high >= fill
        e = b.high >= extend if up_gap else b.low <= extend
        if f and e:
            return "same_bar"
        if f:
            return "fill"
        if e:
            return "extend"
    return "neither"


def _first_touch(bars: Sequence[Bar], minutes: Sequence[int], level: float, up_gap: bool):
    """Minute of the first bar that trades at `level` coming from above (up gap: low <=
    level) or from below (down gap: high >= level); None if none does."""
    for b, m in zip(bars, minutes, strict=True):
        if (b.low <= level) if up_gap else (b.high >= level):
            return m
    return None


def _filled_by_day3(days: Sequence[CashDay], i: int, level: float, up_gap: bool, horizon: int):
    """True / False / None: did one of the `horizon` regular days from day i (day i included,
    early closes skipped) trade at `level`? None if a data hole or the end of the data comes
    before the answer is known."""
    seen = 0
    for day in days[i:]:
        if day.cls == EARLY_CLOSE:
            continue
        if day.cls != REGULAR:
            return None
        if _first_touch(day.bars, day.minutes, level, up_gap) is not None:
            return True
        seen += 1
        if seen == horizon:
            return False
    return None


def _weekdays_between(a: date, b: date) -> int:
    return sum((a + timedelta(days=k)).weekday() < 5 for k in range(1, (b - a).days))


def day_records(days: Sequence[CashDay], cfg: OpenGapConfig | None = None):
    """(records, exclusions): one record per regular day with a regular previous day and a
    known ATR, and one {date, reason} per day that is left out (early_close,
    first_bar_missing, data_hole, atr_warmup, prev_not_regular)."""
    cfg = cfg or OpenGapConfig()
    regular = [d for d in days if d.cls == REGULAR]
    atr_by_date = dict(
        zip((d.date for d in regular), _atr_before(regular, cfg.atr_period), strict=True)
    )
    first30 = cfg.minute_of(cfg.first_window_end)
    at11 = cfg.minute_of(cfg.feature_time)
    last_hour = cfg.minute_of(cfg.last_hour_start)
    records, excl = [], []
    last_full: CashDay | None = None  # the last day that was not an early close
    for i, day in enumerate(days):
        if day.cls != REGULAR:
            excl.append({"date": day.date, "reason": day.cls})
            if day.cls != EARLY_CLOSE:
                last_full = day
            continue
        prev, last_full = last_full, day
        atr = atr_by_date[day.date]
        if atr is None or atr <= 0:
            excl.append({"date": day.date, "reason": "atr_warmup"})
            continue
        if prev is None or prev.cls != REGULAR:
            excl.append({"date": day.date, "reason": "prev_not_regular"})
            continue
        records.append(_record(days, i, day, prev, atr, cfg, (first30, at11, last_hour)))
    return records, excl


def _before(bars: Sequence[Bar], minutes: Sequence[int], limit: int) -> list[Bar]:
    """The bars that opened before minute `limit` after the cash open."""
    return [b for b, m in zip(bars, minutes, strict=True) if m < limit]


def _record(days, i, day, prev, atr, cfg, marks) -> dict:
    first30, at11, last_hour = marks
    bars, mins = day.bars, day.minutes
    prev_close = prev.bars[-1].close
    open_ = bars[0].open
    close = bars[-1].close
    gap = open_ - prev_close
    gap_atr = abs(gap) / atr
    flat = gap_atr < cfg.min_gap_atr
    up_gap = gap > 0
    highs = [b.high for b in bars]
    lows = [b.low for b in bars]
    day_high, day_low = max(highs), min(lows)
    rng = day_high - day_low
    early = _before(bars, mins, first30)
    until11 = _before(bars, mins, at11)
    c30 = early[-1].close if early else None
    rec: dict = {
        "date": day.date,
        "year": day.date.year,
        "half": cfg.half(day.date.year),
        "weekday": f"{day.date.weekday() + 1} {WEEKDAY_NAMES[day.date.weekday()]}",
        "month_part": month_part(day.date),
        "open": open_,
        "prev_close": prev_close,
        "skipped_days": _weekdays_between(prev.date, day.date) if prev.date < day.date else 0,
        "atr": atr,
        "gap": gap,
        "gap_atr": gap_atr,
        "gap_dir": "flat" if flat else ("up" if up_gap else "down"),
        "gap_bucket": "flat" if flat else cfg.bucket(gap_atr),
        "flat": flat,
    }
    # --- features known by the feature time
    rec["first30_atr"] = (c30 - prev_close) / atr if c30 is not None else None
    touch11 = _first_touch(until11, [m for m in mins if m < at11], prev_close, up_gap)
    rec["filled_by_11"] = None if flat else touch11 is not None
    hi30 = max((b.high for b in early), default=None)
    lo30 = min((b.low for b in early), default=None)
    mid = [b for b, m in zip(bars, mins, strict=True) if first30 <= m < at11]
    rec["new_extreme_10_11"] = (
        any(b.high > hi30 or b.low < lo30 for b in mid) if hi30 is not None and mid else None
    )
    if until11:
        h11, l11 = max(b.high for b in until11), min(b.low for b in until11)
        rec["pos_11"] = (until11[-1].close - l11) / (h11 - l11) if h11 > l11 else None
    else:
        rec["pos_11"] = None
    # --- outcomes of the day
    if flat:
        rec.update(
            filled_same_day=None,
            fill_minute=None,
            filled_by_day3=None,
            extend_same_day=None,
            first_touch=None,
        )
    else:
        minute = _first_touch(bars, mins, prev_close, up_gap)
        extend = open_ + gap
        rec["filled_same_day"] = minute is not None
        rec["fill_minute"] = minute
        rec["filled_by_day3"] = (
            True if minute is not None
            else _filled_by_day3(days, i, prev_close, up_gap, cfg.fill_horizon_days)
        )  # fmt: skip
        rec["first_touch"] = _first_of_two(bars, prev_close, extend, up_gap)
        rec["extend_same_day"] = any(
            (b.high >= extend) if up_gap else (b.low <= extend) for b in bars
        )
    rest = close - c30 if c30 is not None else None
    rec["rest_atr"] = rest / atr if rest is not None else None
    f30 = rec["first30_atr"]
    rec["continued"] = (
        None if not f30 or not rest else (f30 > 0) == (rest > 0)
    )  # a zero move on either side is neither
    rec["range"] = rng
    if rng > 0:
        frac = cfg.trend_extreme_frac * rng
        up = open_ - day_low <= frac and day_high - close <= frac
        down = day_high - open_ <= frac and close - day_low <= frac
        rec["trend"] = TREND_UP if up else TREND_DOWN if down else TREND_NONE
        rec["trend_day"] = up or down
        rec["close_pos"] = (close - day_low) / rng
    else:
        rec.update(trend=None, trend_day=None, close_pos=None)
    hi_i, lo_i = highs.index(day_high), lows.index(day_low)  # first bar: ties go to the earliest
    for name, idx in (("high", hi_i), ("low", lo_i)):
        m = mins[idx]
        rec[f"{name}_minute"] = m
        rec[f"{name}_in_first90"] = m < cfg.extreme_window_min
        rec[f"{name}_in_first_hour"] = m < cfg.first_hour_min
        rec[f"{name}_in_last_hour"] = m >= last_hour
    rec.update(_last_hour(bars, mins, last_hour, close, atr))
    return rec


def _last_hour(bars, mins, start: int, close: float, atr: float) -> dict:
    """The first new high / low of the day in the last hour (against everything before it)."""
    prior = [b for b, m in zip(bars, mins, strict=True) if m < start]
    late = [b for b, m in zip(bars, mins, strict=True) if m >= start]
    if not prior or not late:
        return {"last_hour_event": EVENT_NONE, "last_hour_move_atr": None}
    level_hi, level_lo = max(b.high for b in prior), min(b.low for b in prior)
    new_hi = any(b.high > level_hi for b in late)
    new_lo = any(b.low < level_lo for b in late)
    if new_hi and new_lo:
        return {"last_hour_event": EVENT_BOTH, "last_hour_move_atr": None}
    if new_hi:
        return {"last_hour_event": EVENT_HIGH, "last_hour_move_atr": (close - level_hi) / atr}
    if new_lo:
        return {"last_hour_event": EVENT_LOW, "last_hour_move_atr": (level_lo - close) / atr}
    return {"last_hour_event": EVENT_NONE, "last_hour_move_atr": None}


def missing_weekdays(days: Sequence[CashDay]) -> list[date]:
    """Weekdays between the first and the last cash day that have no cash bar at all
    (holidays when the CFD does not trade, data gaps)."""
    if not days:
        return []
    have = {d.date for d in days}
    first = min(have)
    span = (max(have) - first).days
    return [
        d
        for d in (first + timedelta(days=k) for k in range(span + 1))
        if d.weekday() < 5 and d not in have  # Monday..Friday
    ]


# --- small statistics --------------------------------------------------------------------------------


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float | None, float | None]:
    """Wilson score interval of a share k / n (95 % at z = 1.96)."""
    if n <= 0:
        return None, None
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def arcsine_share(fraction: float) -> float:
    """Share of random-walk paths whose maximum (or minimum) falls in the first `fraction` of
    the period: 2 / pi x asin(sqrt(fraction)) (the arcsine law; symmetric in time)."""
    f = min(1.0, max(0.0, fraction))
    return 2 / math.pi * math.asin(math.sqrt(f))


def mean_t(values: Sequence[float]) -> tuple[float | None, float | None]:
    """(mean, t of the mean against 0); t is None for fewer than 2 values or no variance."""
    n = len(values)
    if n == 0:
        return None, None
    mean = sum(values) / n
    if n < 2:
        return mean, None
    var = sum((v - mean) ** 2 for v in values) / (n - 1)
    return mean, (mean / math.sqrt(var / n) if var > 0 else None)


# --- summaries (rows for the CSV files and the printed tables) -----------------------------------------


def _halves(cfg: OpenGapConfig) -> tuple[str, ...]:
    return (*cfg.half_labels, "all")


def _in_half(records: Sequence[dict], half: str) -> list[dict]:
    return list(records) if half == "all" else [r for r in records if r["half"] == half]


def _share_row(k: int, n: int) -> dict:
    lo, hi = wilson(k, n)
    return {"n": n, "k": k, "share": k / n if n else None, "ci_low": lo, "ci_high": hi}


def summarize_gaps(records: Sequence[dict], cfg: OpenGapConfig | None = None) -> list[dict]:
    """Per half x direction (up / down / both) x bucket (+ "all"): days, same-day fill share
    (with its Wilson interval), by-day-3 share (days with a known answer) and the extend
    baseline (same-size move in the gap direction). Flat gaps are counted in their own row."""
    cfg = cfg or OpenGapConfig()
    rows = []
    for half in _halves(cfg):
        sub = _in_half(records, half)
        rows.append(
            {"half": half, "direction": "flat", "bucket": "flat", "n": sum(r["flat"] for r in sub)}
        )
        live = [r for r in sub if not r["flat"]]
        for direction in ("up", "down", "both"):
            d_rows = [r for r in live if direction == "both" or r["gap_dir"] == direction]
            for bucket in (*cfg.bucket_labels(), "all"):
                g = [r for r in d_rows if bucket == "all" or r["gap_bucket"] == bucket]
                if not g:
                    continue
                known3 = [r for r in g if r["filled_by_day3"] is not None]
                same = _share_row(sum(r["filled_same_day"] for r in g), len(g))
                rows.append(
                    {
                        "half": half, "direction": direction, "bucket": bucket, "n": len(g),
                        "same_day_fill": same["share"],
                        "same_day_ci_low": same["ci_low"], "same_day_ci_high": same["ci_high"],
                        "n_day3_known": len(known3),
                        "by_day3_fill": (
                            sum(r["filled_by_day3"] for r in known3) / len(known3) if known3 else None
                        ),
                        "extend_same_day": sum(r["extend_same_day"] for r in g) / len(g),
                        **{
                            name: sum(r["first_touch"] == key for r in g) / len(g)
                            for name, key in (
                                ("fill_first", "fill"),
                                ("extend_first", "extend"),
                                ("same_bar", "same_bar"),
                                ("neither", "neither"),
                            )
                        },
                    }
                )  # fmt: skip
    return rows


def summarize_first30(records: Sequence[dict], cfg: OpenGapConfig | None = None) -> list[dict]:
    """Per half x gap bucket (+ "all"): days with a first-30-minutes move and a rest-of-day
    move, the share where the rest continued the first 30 minutes, and the mean rest-of-day
    move in the direction of the first 30 minutes in ATR (with its t)."""
    cfg = cfg or OpenGapConfig()
    rows = []
    for half in _halves(cfg):
        sub = [r for r in _in_half(records, half) if r["first30_atr"] is not None]
        for bucket in ("all", "flat", *cfg.bucket_labels()):
            g = [r for r in sub if bucket == "all" or r["gap_bucket"] == bucket]
            moves = [r for r in g if r["continued"] is not None]
            if not moves:
                continue
            signed = [r["rest_atr"] * (1 if r["first30_atr"] > 0 else -1) for r in moves]
            mean, t = mean_t(signed)
            cont = _share_row(sum(r["continued"] for r in moves), len(moves))
            rows.append(
                {
                    "half": half, "bucket": bucket, "n": len(moves),
                    "continuation_share": cont["share"],
                    "ci_low": cont["ci_low"], "ci_high": cont["ci_high"],
                    "mean_rest_signed_atr": mean, "t": t,
                }
            )  # fmt: skip
    return rows


def _trend_features(cfg: OpenGapConfig):
    f = cfg.pos_extreme_frac
    return {
        "(none)": lambda r: True,
        "gap_unfilled_at_11": lambda r: r["filled_by_11"] is False,
        "new_extreme_10_11": lambda r: bool(r["new_extreme_10_11"]),
        "pos_11_in_extreme_fifth": lambda r: (
            r["pos_11"] is not None and (r["pos_11"] <= f or r["pos_11"] >= 1 - f)
        ),
    }


def summarize_trend(records: Sequence[dict], cfg: OpenGapConfig | None = None) -> list[dict]:
    """Per half x group (all / weekday / month part) x feature known at 11:00: days, trend
    days, share with its Wilson interval and the lift over the group's base rate."""
    cfg = cfg or OpenGapConfig()
    features = _trend_features(cfg)
    rows = []
    for half in _halves(cfg):
        sub = [r for r in _in_half(records, half) if r["trend_day"] is not None]
        groups = {"all": sub}
        for r in sub:
            groups.setdefault(f"weekday {r['weekday']}", []).append(r)
            groups.setdefault(f"month {r['month_part']}", []).append(r)
        for group, g in groups.items():
            base = sum(r["trend_day"] for r in g) / len(g) if g else None
            for name, fn in features.items():
                hit = [r for r in g if fn(r)]
                if not hit:
                    continue
                row = _share_row(sum(r["trend_day"] for r in hit), len(hit))
                rows.append(
                    {
                        "half": half, "group": group, "feature": name, "n": row["n"],
                        "trend_days": row["k"], "share": row["share"],
                        "ci_low": row["ci_low"], "ci_high": row["ci_high"],
                        "base_share": base,
                        "lift": row["share"] / base if base else None,
                    }
                )  # fmt: skip
    return rows


def summarize_extremes(records: Sequence[dict], cfg: OpenGapConfig | None = None) -> list[dict]:
    """Per half: the share of days whose high, low, either or both printed in the first 90
    minutes / first hour / last hour, next to the uniform share and the random-walk
    (arcsine) share of that window."""
    cfg = cfg or OpenGapConfig()
    total = cfg.session_minutes
    windows = (
        ("first_90_min", "first90", cfg.extreme_window_min / total),
        ("first_hour", "first_hour", cfg.first_hour_min / total),
        ("last_hour", "last_hour", (total - cfg.minute_of(cfg.last_hour_start)) / total),
    )
    rows = []
    for half in _halves(cfg):
        sub = _in_half(records, half)
        if not sub:
            continue
        for label, key, frac in windows:
            hi = [r[f"high_in_{key}"] for r in sub]
            lo = [r[f"low_in_{key}"] for r in sub]
            n = len(sub)
            rows.append(
                {
                    "half": half, "window": label, "n": n,
                    "high_share": sum(hi) / n, "low_share": sum(lo) / n,
                    "either_share": sum(h or lw for h, lw in zip(hi, lo, strict=True)) / n,
                    "both_share": sum(h and lw for h, lw in zip(hi, lo, strict=True)) / n,
                    "uniform_share": frac, "random_walk_share": arcsine_share(frac),
                }
            )  # fmt: skip
    return rows


def summarize_last_hour(records: Sequence[dict], cfg: OpenGapConfig | None = None) -> list[dict]:
    """Per half x event (new high / low / both / none in the last hour): days and the mean
    close position in the day's range, and for single events the mean move from the old
    extreme to the close in ATR (positive = continued in the event's direction)."""
    cfg = cfg or OpenGapConfig()
    rows = []
    for half in _halves(cfg):
        sub = [r for r in _in_half(records, half) if r["close_pos"] is not None]
        for event in (EVENT_HIGH, EVENT_LOW, EVENT_BOTH, EVENT_NONE, "all days"):
            g = [r for r in sub if event == "all days" or r["last_hour_event"] == event]
            if not g:
                continue
            moves = [r["last_hour_move_atr"] for r in g if r["last_hour_move_atr"] is not None]
            mean_move, t = mean_t(moves)
            rows.append(
                {
                    "half": half, "event": event, "n": len(g),
                    "mean_close_pos": sum(r["close_pos"] for r in g) / len(g),
                    "mean_move_atr": mean_move, "move_t": t,
                }
            )  # fmt: skip
    return rows
