"""Robustness measures on R trade lists and on grids of variants. Spec: ROADMAP.md › 6.4;
background and defaults: knowledge/topics/testing-and-robustness.md (Kaufman, *Trading
Systems and Methods*, ch. 21).

Pure functions on anything with the trade attributes they read (`symbol`, `entry_time`,
`exit_time`, `r_gross`, `r_net`): engine `TradeResult`s and `TradeRecord`s.

Over a grid of variants (the net R of each):
- `grid_stats`: share of profitable variants (robust at >= `robust_share`, Kaufman 70 %),
  mean, sample st.dev and mean - 1 sd (the adjusted expectation);
- `smooth_series` / `smooth_grid`: each cell replaced by the mean of itself and its
  neighbours; `plateau_index` / `plateau_cell`: the best smoothed cell, so a lone spike loses
  to a broad plateau.

Over one trade list (`trade_robustness`):
- the two halves (entry year <= `first_half_end_year`) and Welch's t between their trade R;
- kurtosis of the daily R (days with a closing trade only; normal = 3; above
  `kurtosis_warn` is an overfit warning);
- net R without the best trade;
- stressed costs: the cost of each trade (`r_gross - r_net`, spread + commission + swap)
  times `cost_stress`; swap income (net above gross) is not scaled;
- shock days (`shock_dates`, `shock_report`): a day whose true range is more than
  `shock_range_atr` times the mean true range of the `shock_atr_period` days before it;
  trades are attributed to the UTC date they exit on. If more than half of the shock days
  with a closing trade were profitable, the risk is understated (Kaufman p.970-975).
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date

from backtester.analytics.metrics import by_exit


def monthly_net(trades) -> dict[str, float]:
    """UTC entry-month net R, filling gaps. Spec: research-runner.md > Runner checks (V2.4c)."""
    totals = {}
    for trade in trades:
        entry = trade.entry_time.astimezone(UTC)
        month = entry.year * 12 + entry.month - 1
        totals[month] = totals.get(month, 0.0) + trade.r_net
    if not totals:
        return {}
    return {
        f"{month // 12:04d}-{month % 12 + 1:02d}": totals.get(month, 0.0)
        for month in range(min(totals), max(totals) + 1)
    }


def returns_slope(monthly: Mapping) -> dict:
    """OLS on chronological monthly R; slope and SE in R/year, perfect-fit SE/t are null.

    Spec: research-runner.md > Runner checks (V2.4c). At least six months are required.
    """
    values = [monthly[k] for k in sorted(monthly)]
    n = len(values)
    out = {
        "n_months": n,
        "slope_per_year": None,
        "standard_error": None,
        "t_stat": None,
        "perfect_fit": False,
    }
    if n < 6:
        return out
    x_mean = (n - 1) / 2
    mean = sum(values) / n
    sxx = sum((i - x_mean) ** 2 for i in range(n))
    slope = sum((i - x_mean) * (v - mean) for i, v in enumerate(values)) / sxx
    residual = sum((v - mean - slope * (i - x_mean)) ** 2 for i, v in enumerate(values))
    out["slope_per_year"] = slope * 12
    if residual == 0:
        out["perfect_fit"] = True
    else:
        se = math.sqrt(residual / (n - 2) / sxx)
        out.update(standard_error=se * 12, t_stat=slope / se)
    return out


def top_trades(trades, n=10) -> list[dict]:
    """Best/worst R, ties by entry time. Spec: research-runner.md > Runner checks (V2.4c)."""
    trades = list(trades)
    rows = []
    for side, sign in (("best", -1), ("worst", 1)):
        ordered = sorted(trades, key=lambda t: (sign * t.r_net, t.entry_time))[:n]
        for rank, trade in enumerate(ordered, 1):
            direction = getattr(trade.direction, "value", trade.direction)
            # Use the same labels for engine enums and persisted long/short records.
            direction = {"bullish": "long", "bearish": "short"}.get(direction, direction)
            reason = getattr(trade, "exit_reason", "")
            rows.append(
                {
                    "rank": rank,
                    "side": side,
                    "symbol": trade.symbol,
                    "direction": direction,
                    "entry_time": trade.entry_time.astimezone(UTC).isoformat(),
                    "exit_time": trade.exit_time.astimezone(UTC).isoformat(),
                    "exit_reason": getattr(reason, "value", reason),
                    "r_net": trade.r_net,
                    "hold_hours": (trade.exit_time - trade.entry_time).total_seconds() / 3600,
                }
            )
    return rows


def extreme_summary(trades, n=10) -> dict:
    """Net R contribution of the best n. Spec: research-runner.md > Runner checks (V2.4c)."""
    values = sorted((t.r_net for t in trades), reverse=True)
    total, best = sum(values), sum(values[:n])
    return {
        "net_r": total,
        "net_r_without_best": total - best,
        "best_share": best / total if total > 0 else None,
    }


@dataclass(frozen=True, slots=True)
class RobustnessConfig:
    robust_share: float = 0.70  # share of profitable variants that counts as robust
    cost_stress: float = 1.5  # stressed costs = cost x this
    shock_atr_period: int = 10  # days before the day, for the mean true range
    shock_range_atr: float = 3.5  # shock day: true range > this x that mean
    kurtosis_warn: float = 7.0  # daily-R kurtosis above this = overfit warning (normal 3)
    first_half_end_year: int = 2022  # halves 2020-22 / 2023-26 as in tools/trend_grid
    t_critical: float = 2.0  # |Welch t| at or above this = the halves differ

    def __post_init__(self) -> None:
        if not 0 < self.robust_share <= 1:
            raise ValueError("robust_share must be in (0, 1]")
        if self.cost_stress < 1:
            raise ValueError("cost_stress must be >= 1")
        if self.shock_atr_period < 1:
            raise ValueError("shock_atr_period must be >= 1")
        if self.shock_range_atr <= 0:
            raise ValueError("shock_range_atr must be > 0")


# --- grids of variants ---------------------------------------------------------------------


def profitable_share(values: Iterable[float]) -> float | None:
    """Share of the values above 0 (None for no values)."""
    values = list(values)
    return sum(v > 0 for v in values) / len(values) if values else None


def grid_stats(values: Sequence[float], config: RobustnessConfig | None = None) -> dict:
    """n, mean, sample st.dev, mean - 1 sd, share profitable and the robust flag."""
    cfg = config or RobustnessConfig()
    n = len(values)
    if n == 0:
        return {
            "n": 0, "mean": None, "std": None, "adjusted": None,
            "profitable_share": None, "robust": False,
        }  # fmt: skip
    mean = sum(values) / n
    std = math.sqrt(sum((v - mean) ** 2 for v in values) / (n - 1)) if n > 1 else 0.0
    share = profitable_share(values)
    return {
        "n": n,
        "mean": mean,
        "std": std,
        "adjusted": mean - std,
        "profitable_share": share,
        "robust": share is not None and share >= cfg.robust_share,
    }


def smooth_series(values: Sequence[float | None]) -> list[float | None]:
    """Each value replaced by the mean of itself and its two neighbours (edges: the ones
    that exist). Missing values (None) stay None and are not counted."""
    out: list[float | None] = []
    for i, v in enumerate(values):
        if v is None:
            out.append(None)
            continue
        near = [values[j] for j in (i - 1, i, i + 1) if 0 <= j < len(values)]
        near = [x for x in near if x is not None]
        out.append(sum(near) / len(near))
    return out


def smooth_grid(grid: Sequence[Sequence[float | None]]) -> list[list[float | None]]:
    """Each cell replaced by the mean of its 3 x 3 neighbourhood (edges: the cells that
    exist, so an edge cell is damped by fewer neighbours). Missing cells stay None and are
    not counted."""
    rows = len(grid)
    out: list[list[float | None]] = []
    for r in range(rows):
        line: list[float | None] = []
        for c in range(len(grid[r])):
            if grid[r][c] is None:
                line.append(None)
                continue
            near = [
                grid[rr][cc]
                for rr in range(max(0, r - 1), min(rows, r + 2))
                for cc in range(max(0, c - 1), min(len(grid[rr]), c + 2))
            ]
            near = [x for x in near if x is not None]
            line.append(sum(near) / len(near))
        out.append(line)
    return out


def plateau_index(values: Sequence[float | None]) -> int | None:
    """Index of the best smoothed value (the first one on a tie); None without values."""
    smooth = smooth_series(values)
    best = None
    for i, v in enumerate(smooth):
        if v is not None and (best is None or v > smooth[best]):
            best = i
    return best


def plateau_cell(grid: Sequence[Sequence[float | None]]) -> tuple[int, int] | None:
    """(row, column) of the best smoothed cell (the first on a tie)."""
    smooth = smooth_grid(grid)
    best, best_v = None, None
    for r, line in enumerate(smooth):
        for c, v in enumerate(line):
            if v is not None and (best_v is None or v > best_v):
                best, best_v = (r, c), v
    return best


# --- one trade list -----------------------------------------------------------------------------


def welch_t(a: Sequence[float], b: Sequence[float], config: RobustnessConfig | None = None):
    """Welch's t-test between two samples: {t, df, mean_a, mean_b, significant}, t =
    (mean_a - mean_b) / se. None with fewer than 2 values in a sample or no variance."""
    cfg = config or RobustnessConfig()
    if len(a) < 2 or len(b) < 2:
        return None
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    va = sum((x - ma) ** 2 for x in a) / (len(a) - 1)
    vb = sum((x - mb) ** 2 for x in b) / (len(b) - 1)
    sa, sb = va / len(a), vb / len(b)
    if sa + sb == 0:
        return None
    t = (ma - mb) / math.sqrt(sa + sb)
    denom = sa**2 / (len(a) - 1) + sb**2 / (len(b) - 1)
    df = (sa + sb) ** 2 / denom
    return {
        "t": t, "df": df, "mean_a": ma, "mean_b": mb, "significant": abs(t) >= cfg.t_critical,
    }  # fmt: skip


def kurtosis(values: Sequence[float]) -> float | None:
    """m4 / m2^2 of the values (normal = 3); None for fewer than 4 values or no variance.
    Used on `daily_r`, which has only the days a trade closed on: padding the idle days with
    zeros would push every sparse system far above the warning level."""
    n = len(values)
    if n < 4:
        return None
    mean = sum(values) / n
    m2 = sum((v - mean) ** 2 for v in values) / n
    if m2 == 0:
        return None
    return (sum((v - mean) ** 4 for v in values) / n) / m2**2


def daily_r(trades: Sequence) -> list[float]:
    """Net R summed per UTC exit date, in date order."""
    sums: dict[date, float] = {}
    for t in by_exit(trades):
        d = t.exit_time.date()
        sums[d] = sums.get(d, 0.0) + t.r_net
    return [sums[d] for d in sorted(sums)]


def without_best(trades: Sequence) -> dict:
    """{net, best, net_without_best}: the sum of net R and without the single best trade."""
    net = sum(t.r_net for t in trades)
    best = max((t.r_net for t in trades), default=0.0)
    return {"net": net, "best": best, "net_without_best": net - best if trades else 0.0}


def stressed_net(trades: Iterable, factor: float) -> float:
    """Sum of net R with each trade's cost (`r_gross - r_net`) multiplied by `factor`.
    A trade whose net is above its gross (swap income) is left as it is."""
    if factor < 1:
        raise ValueError("factor must be >= 1")
    total = 0.0
    for t in trades:
        cost = t.r_gross - t.r_net
        total += t.r_gross - factor * cost if cost > 0 else t.r_net
    return total


# --- shock days -----------------------------------------------------------------------------------


def shock_dates(
    days: Sequence[tuple[date, float, float, float]], config: RobustnessConfig | None = None
) -> set[date]:
    """Shock days of daily bars `(date, high, low, close)` in date order: the true range is
    more than `shock_range_atr` x the mean true range of the `shock_atr_period` days before
    it (so a shock never raises its own threshold). No shock until there are that many days."""
    cfg = config or RobustnessConfig()
    ranges: list[float] = []
    prev_close: float | None = None
    shocks: set[date] = set()
    n = cfg.shock_atr_period
    for d, high, low, close in days:
        tr = high - low
        if prev_close is not None:
            tr = max(tr, abs(high - prev_close), abs(low - prev_close))
        if len(ranges) >= n and tr > cfg.shock_range_atr * (sum(ranges[-n:]) / n):
            shocks.add(d)
        ranges.append(tr)
        prev_close = close
    return shocks


def shock_report(trades: Sequence, shocks: Mapping[str, set[date]]) -> dict:
    """The result by shock day. A trade belongs to the UTC date it exits on and to the shock
    set of its own symbol. `shock_days_with_trades` counts (symbol, date) pairs that had a
    trade closing; `profitable_share` is the share of them with a net P/L above 0 and
    `understated_risk` is true above one half. `net_r_shocks_reversed` flips the sign of the
    shock days' result (what the sum would be if the shocks had gone the other way)."""
    pnl: dict[tuple[str, date], float] = {}
    total = 0.0
    for t in trades:
        total += t.r_net
        d = t.exit_time.date()
        if d in shocks.get(t.symbol, ()):
            pnl[t.symbol, d] = pnl.get((t.symbol, d), 0.0) + t.r_net
    shock_net = sum(pnl.values())
    profitable = sum(v > 0 for v in pnl.values())
    share = profitable / len(pnl) if pnl else None
    return {
        "shock_days_with_trades": len(pnl),
        "shock_days_profitable": profitable,
        "profitable_share": share,
        "understated_risk": share is not None and share > 0.5,
        "net_r_total": total,
        "net_r_shock_days": shock_net,
        "net_r_without_shocks": total - shock_net,
        "net_r_shocks_reversed": total - 2 * shock_net,
    }


# --- the report of one trade list ---------------------------------------------------------------------


def trade_robustness(
    trades: Sequence,
    config: RobustnessConfig | None = None,
    shocks: Mapping[str, set[date]] | None = None,
) -> dict:
    """One flat row of all the measures above for a trade list (shock measures only with
    `shocks`)."""
    cfg = config or RobustnessConfig()
    first = [t for t in trades if t.entry_time.year <= cfg.first_half_end_year]
    second = [t for t in trades if t.entry_time.year > cfg.first_half_end_year]
    welch = welch_t([t.r_net for t in first], [t.r_net for t in second], cfg)
    kurt = kurtosis(daily_r(trades))
    best = without_best(trades)
    row = {
        "trades": len(trades),
        "net_r": best["net"],
        "net_r_without_best": best["net_without_best"],
        "net_r_stressed": stressed_net(trades, cfg.cost_stress),
        "half_first_trades": len(first),
        "half_second_trades": len(second),
        "half_first_net_r": sum(t.r_net for t in first),
        "half_second_net_r": sum(t.r_net for t in second),
        "welch_t": welch["t"] if welch else None,
        "welch_df": welch["df"] if welch else None,
        "welch_significant": bool(welch and welch["significant"]),
        "kurtosis_daily": kurt,
        "kurtosis_flag": kurt is not None and kurt > cfg.kurtosis_warn,
    }
    if shocks is not None:
        rep = shock_report(trades, shocks)
        row.update({k: v for k, v in rep.items() if k not in ("net_r_total",)})
    return row
