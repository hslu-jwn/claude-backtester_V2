"""Metrics on lists of closed trades (R multiples). Spec: ROADMAP.md › 3.4, 3.6.

Works on anything with the trade attributes it reads: engine `TradeResult`s (the run's
summary.json) and `TradeRecord`s read back from trades.csv (the results page).

`summarize` gives the summary of a backtest run:
- trades; wins / losses / break-evens and the win rate, by the net result (after costs):
  win r_net > 0, loss r_net < 0, break-even |r_net| < `BREAK_EVEN_TOL` (a SL moved to
  break-even with costs ends at 0R net);
- net R gross (chart prices, no costs) and net (after spread and commission), and the
  average realized R per trade, gross and net;
- expectancy: the average net R per trade (= win rate x average win + loss rate x average
  loss, break-evens add 0);
- average win / average loss: mean net R of the wins / of the losses (the loss is < 0);
- profit factor: net R of the wins / |net R of the losses| (None without a loss);
- average R:R: the planned R if every TP is hit (`planned_r`, share-weighted);
- max drawdown in R, gross and net: the deepest fall of the cumulative R from its peak
  (starting at 0), with trades counted when they close (exit time order); trades closing
  at the same time count as one step (their order inside a candle is unknown), as in
  `equity_curve`;
- longest losing / winning streak: most losses (wins) in a row in exit time order; a
  break-even ends a streak.

`split` groups trades by a key (`by_symbol`, `by_session`, …) and summarizes each group
(first-seen order, or the key's own `rank` order for the time keys `by_hour`, `by_weekday`,
`by_month_part`, `by_ny_window`, ROADMAP 6.5);
`by_period` gives per year / quarter (ROADMAP 6.3) the summary of all trades and of each
symbol; `equity_curve` and `r_histogram` feed the results page's charts.
"""

from __future__ import annotations

import calendar
import math
from collections.abc import Callable, Iterable, Sequence
from datetime import time as day_time
from zoneinfo import ZoneInfo

BREAK_EVEN_TOL = 1e-9
TP_OUTCOMES = (
    "TP1 + TP2", "TP1, rest out", "TP (one target)", "no TP", "TP1 + TP2 + TP3",
    "TP1 + TP2, rest out",
)  # fmt: skip
LAST_MINUTES_TAG = "last_90m"  # strategy/session_zone_sweep (no import: analytics is shared)


def max_drawdown(results: Iterable[float]) -> float:
    """Deepest drop of the running sum below its peak (peak starts at 0), as a value >= 0."""
    equity = peak = worst = 0.0
    for r in results:
        equity += r
        peak = max(peak, equity)
        worst = max(worst, peak - equity)
    return worst


def longest_streak(results: Iterable[float], sign: int) -> int:
    """Most results in a row with that sign (-1: losses, +1: wins); a break-even ends it."""
    best = run = 0
    for r in results:
        run = run + 1 if sign * r > BREAK_EVEN_TOL else 0
        best = max(best, run)
    return best


def by_exit(trades: Sequence) -> list:
    """Trades in the order they closed (same time: entry time, then symbol)."""
    return sorted(trades, key=lambda t: (t.exit_time, t.entry_time, t.symbol))


def per_exit_time(trades: Sequence, attr: str) -> list[float]:
    """Sum of `attr` (r_gross / r_net) of the trades closing at each exit time, in order."""
    sums: dict = {}
    for t in by_exit(trades):
        sums[t.exit_time] = sums.get(t.exit_time, 0.0) + getattr(t, attr)
    return list(sums.values())


def _mean(values: Sequence[float]) -> float | None:
    return sum(values) / len(values) if values else None


def summarize(trades: Sequence) -> dict:
    n = len(trades)
    win_r = [t.r_net for t in trades if t.r_net > BREAK_EVEN_TOL]
    loss_r = [t.r_net for t in trades if t.r_net < -BREAK_EVEN_TOL]
    ordered = by_exit(trades)
    net_gross = sum(t.r_gross for t in trades)
    net = sum(t.r_net for t in trades)
    return {
        "trades": n,
        "wins": len(win_r),
        "losses": len(loss_r),
        "break_even": n - len(win_r) - len(loss_r),
        "win_rate": len(win_r) / n if n else None,
        "net_r_gross": net_gross,
        "net_r_net": net,
        "avg_r_gross": net_gross / n if n else None,
        "avg_r_net": net / n if n else None,
        "expectancy_r": net / n if n else None,
        "avg_win_r": _mean(win_r),
        "avg_loss_r": _mean(loss_r),
        "profit_factor": sum(win_r) / -sum(loss_r) if loss_r else None,
        "avg_rr": _mean([t.planned_r for t in trades if t.planned_r is not None]),
        "max_drawdown_r_gross": max_drawdown(per_exit_time(trades, "r_gross")),
        "max_drawdown_r_net": max_drawdown(per_exit_time(trades, "r_net")),
        "longest_losing_streak": longest_streak((t.r_net for t in ordered), -1),
        "longest_winning_streak": longest_streak((t.r_net for t in ordered), 1),
    }


# --- splits ----------------------------------------------------------------------------


def by_symbol(t) -> str:
    return t.symbol


def by_session(t) -> str:
    """The session the trade was entered in ("london 2026-09-02" -> "london")."""
    return t.session.split(" ")[0] if t.session else "none"


def by_direction(t) -> str:
    return t.direction


def by_confluence(t) -> str:
    return t.confluence or "unknown"


def tp_outcome(t) -> str:
    """Two targets: both hit, TP1 only (the rest closed at break-even / SL / end of data)
    or none; three: all, TP1 + TP2, TP1 only or none; one target: hit or not. `parts` as in trades.csv (dicts with a "reason")."""
    hits = sum(p["reason"] == "take_profit" for p in t.parts)
    if hits == 0:
        return TP_OUTCOMES[3]
    if t.take_profit_2 is None:
        return TP_OUTCOMES[2]
    if t.take_profit_3 is not None and hits >= 2:  # three targets (strategy 2)
        return TP_OUTCOMES[4] if hits >= 3 else TP_OUTCOMES[5]
    return TP_OUTCOMES[0] if hits >= 2 else TP_OUTCOMES[1]


def by_tag(t) -> str:
    """Strategy 1's last-1.5h tag (strategy-session-zones.md › Session filters)."""
    return "last 1.5h" if LAST_MINUTES_TAG in t.tags else "other"


# --- time splits (ROADMAP 6.5; knowledge base I-22) -------------------------------------
# Windows of the New York cash session (Aziz): Open / Midday / Close. A trade is in the
# window of its entry time in New York (DST follows the city); anything else is outside.

NY_ZONE = ZoneInfo("America/New_York")
NY_WINDOWS = (
    ("Open", day_time(9, 30), day_time(11, 0)),
    ("Midday", day_time(11, 0), day_time(15, 0)),
    ("Close", day_time(15, 0), day_time(16, 0)),
)
NY_OUTSIDE = "Outside cash hours"
NY_ORDER = (*(w[0] for w in NY_WINDOWS), NY_OUTSIDE)
MONTH_EDGE_DAYS = 3  # first / last this many weekdays of the month
MONTH_PARTS = ("first 3 days", "mid", "last 3 days")
WEEKDAY_NAMES = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
MAX_WEEKDAY = 4  # Friday; datetime.weekday()


def _ranked(rank: Callable[[str], object]):
    """Mark a split key with the order its groups are listed in (`split` sorts by it)."""

    def mark(fn: Callable) -> Callable:
        fn.rank = rank  # type: ignore[attr-defined]
        return fn

    return mark


@_ranked(str)
def by_hour(t) -> str:
    """The UTC hour of the entry (entry candle close), "08:00 UTC"."""
    return f"{t.entry_time:%H}:00 UTC"


@_ranked(str)
def by_weekday(t) -> str:
    """The UTC weekday of the entry, numbered so it sorts Monday first ("3 Wed")."""
    d = t.entry_time.weekday()
    return f"{d + 1} {WEEKDAY_NAMES[d]}"


def _weekdays_in_month(year: int, month: int) -> list[int]:
    days_in_month = calendar.monthrange(year, month)[1]
    return [
        d for d in range(1, days_in_month + 1) if calendar.weekday(year, month, d) <= MAX_WEEKDAY
    ]


@_ranked(MONTH_PARTS.index)
def by_month_part(t) -> str:
    """ "first 3 days" / "last 3 days" of the entry's month counted in weekdays (no holiday
    calendar), "mid" otherwise. A weekend day counts the weekdays before / after it. The
    first part wins where they overlap."""
    e = t.entry_time
    weekdays = _weekdays_in_month(e.year, e.month)
    before = sum(d <= e.day for d in weekdays)
    after = sum(d >= e.day for d in weekdays)
    if before <= MONTH_EDGE_DAYS:
        return MONTH_PARTS[0]
    if after <= MONTH_EDGE_DAYS:
        return MONTH_PARTS[2]
    return MONTH_PARTS[1]


@_ranked(NY_ORDER.index)
def by_ny_window(t) -> str:
    """ "Open" 9:30-11:00, "Midday" 11:00-15:00, "Close" 15:00-16:00 New York time of the
    entry; otherwise "Outside cash hours"."""
    local = t.entry_time.astimezone(NY_ZONE).time()
    for name, start, end in NY_WINDOWS:
        if start <= local < end:
            return name
    return NY_OUTSIDE


SPLITS: dict[str, Callable] = {
    "Symbol": by_symbol,
    "Session": by_session,
    "Long / short": by_direction,
    "Confluence": by_confluence,
    "TP outcome": tp_outcome,
    "Tag": by_tag,
    "Hour (UTC)": by_hour,
    "Weekday": by_weekday,
    "Month part": by_month_part,
    "NY window": by_ny_window,
}


def by_year(t) -> str:
    """The year the trade was entered in (UTC, entry candle close)."""
    return f"{t.entry_time:%Y}"


def by_quarter(t) -> str:
    return f"{t.entry_time:%Y} Q{(t.entry_time.month - 1) // 3 + 1}"


def by_period(trades: Sequence, key: Callable = by_year) -> dict[str, dict]:
    """{period: {"all": summary, "<symbol>": summary, …}}, periods in time order. A
    period's max drawdown counts only its own trades (starting at 0)."""
    groups: dict[str, list] = {}
    for t in trades:
        groups.setdefault(key(t), []).append(t)
    symbols = sorted({t.symbol for t in trades})
    out = {}
    for period in sorted(groups):
        rows = groups[period]
        out[period] = {"all": summarize(rows)}
        for s in symbols:
            out[period][s] = summarize([t for t in rows if t.symbol == s])
    return out


def split(trades: Sequence, key: Callable) -> dict[str, dict]:
    """{group: summarize(its trades)}, groups in first-seen order (entry order), or sorted
    by the key's `rank` (the time keys)."""
    groups: dict[str, list] = {}
    for t in trades:
        groups.setdefault(key(t), []).append(t)
    rank = getattr(key, "rank", None)
    names = sorted(groups, key=rank) if rank else list(groups)
    return {k: summarize(groups[k]) for k in names}


# --- charts ----------------------------------------------------------------------------


def equity_curve(trades: Sequence) -> list[dict]:
    """Cumulative R at each exit time, gross and net, with the net drawdown (<= 0) below
    the running peak. Starts at 0 at the first entry; trades closing at the same time are
    one point."""
    if not trades:
        return []
    start = min(t.entry_time for t in trades)
    sums: dict = {start: (0.0, 0.0)}
    gross = net = 0.0
    for t in by_exit(trades):
        gross += t.r_gross
        net += t.r_net
        sums[t.exit_time] = (gross, net)  # the last trade closing at a time wins
    points, peak = [], 0.0
    for time, (gross, net) in sums.items():
        peak = max(peak, net)
        points.append({"time": time, "gross": gross, "net": net, "drawdown": net - peak})
    return points


def r_histogram(values: Iterable[float], width: float = 0.5) -> list[dict]:
    """Counts per bin [lo, lo + width), bins aligned to multiples of `width`, every bin from
    the lowest to the highest value (empty ones included)."""
    values = list(values)
    if not values:
        return []
    index = [math.floor(v / width + 1e-9) for v in values]
    counts = dict.fromkeys(range(min(index), max(index) + 1), 0)
    for i in index:
        counts[i] += 1
    return [{"lo": i * width, "hi": (i + 1) * width, "count": c} for i, c in counts.items()]
