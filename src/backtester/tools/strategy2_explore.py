"""Explore strategy 2: entry time, AM vs PM, exit structure and sweep rules, in one place.

    python -m backtester.tools.strategy2_explore collect NAS100 --variant base
    python -m backtester.tools.strategy2_explore report

`collect` runs strategy 2 on one symbol with WIDE windows (AM 08:00-12:30, PM 12:30-17:00
ET, open -90 min to +3 h) and no trade limit, so every entry of the funnel in that range is
recorded with its time, then replays those entries through the engine with different exit
structures (`EXITS`: 3 parts + break-even, TP1 only, fixed R, ...), costs included.
`report` filters the recorded entries to any window (minutes before / after the open, the
setup must start inside it, first trade per window and index only = max trades 1) and
tables net R by AM / PM, entry time and exit structure.

Approximations (read the numbers with them in mind): the bias (4h / 15m trend) is read at
the wide window's start, not at a narrower window's; re-entries after a closed trade
follow the "3 parts + break-even" exits in every exit variant. Research only: it changes no
setting. Spec: strategy-ny-indices.md.
"""

from __future__ import annotations

import argparse
import csv
import pickle
import statistics
from collections import defaultdict
from dataclasses import dataclass, replace
from datetime import date, datetime, time
from pathlib import Path

from backtester.core.models import Direction, Timeframe
from backtester.data.sources import DEFAULT_SOURCES
from backtester.engine.backtest import run_backtest
from backtester.paths import RESULTS_DIR
from backtester.runner import RunSettings, _load
from backtester.strategy.base import Order, Strategy
from backtester.strategy.ny_index_sweep.config import NyIndexSweepConfig
from backtester.strategy.ny_index_sweep.strategy import NyIndexSweep
from backtester.strategy.ny_index_sweep.windows import WindowConfig, WindowTimes
from backtester.tools.strategy2_sweep_grid import VARIANTS

OUT = RESULTS_DIR / "strategy2_explore"
# wide windows around the open, so any narrower window can be cut out afterwards
WIDE = WindowConfig(
    am=WindowTimes(time(8), time(12, 30), time(9, 30), time(9, 50), time(10, 10)),
    pm=WindowTimes(time(12, 30), time(17), time(14), time(13, 50), time(14, 10)),
)
BEFORE_MAX, AFTER_MAX = 90, 180  # minutes of the wide windows around the open


def fixed_r(order: Order, k: float) -> Order:
    """Everything closes at k R (entry +- k x risk), stop loss unchanged."""
    sign = 1 if order.direction is Direction.BULLISH else -1
    target = order.entry + sign * k * abs(order.entry - order.stop_loss)
    return replace(
        order, take_profit=target, take_profit_2=None, take_profit_3=None, tp1_share=1.0,
        tp2_share=None, break_even_after_tp1=False,
    )  # fmt: skip


def single(order: Order, which: int) -> Order:
    """The whole position at TP1 / TP2 / TP3 (the last one there is, if fewer)."""
    tps = [t for t in (order.take_profit, order.take_profit_2, order.take_profit_3) if t]
    return replace(
        order, take_profit=tps[min(which, len(tps)) - 1], take_profit_2=None,
        take_profit_3=None, tp1_share=1.0, tp2_share=None, break_even_after_tp1=False,
    )  # fmt: skip


def two_parts(order: Order) -> Order:
    if order.take_profit_2 is None:
        return order
    return replace(order, take_profit_3=None, tp1_share=0.5, tp2_share=None)


EXITS = {
    "3 parts + BE (today)": lambda o: o,
    "3 parts, no BE": lambda o: replace(o, break_even_after_tp1=False),
    "2 parts + BE": two_parts,
    "TP1 only": lambda o: single(o, 1),
    "TP2 only": lambda o: single(o, 2),
    "1R only": lambda o: fixed_r(o, 1.0),
    "1.5R only": lambda o: fixed_r(o, 1.5),
    "2R only": lambda o: fixed_r(o, 2.0),
    "3R only": lambda o: fixed_r(o, 3.0),
}


class ReplayOrders(Strategy):
    """Hands back recorded orders at their entry candle's close time."""

    base_timeframe = Timeframe.M1
    timeframes = (Timeframe.M1,)
    uses_session_break_even = False

    def __init__(self, orders: dict[datetime, list[Order]]):
        self._orders = orders

    def on_candle(self, now, views):
        return self._orders.get(now, [])


@dataclass
class Entry:
    symbol: str
    variant: str
    at: datetime  # entry time (UTC)
    window: str  # "am" / "pm"
    date: date  # New York trading date
    open_offset: int  # minutes after the index open
    start_offset: int  # window start relative to the open (negative)
    setup_start: int  # the sweep extreme's time relative to the open, minutes
    route: str
    z3: str
    risk: float
    net_r: dict[str, float]  # exit variant -> net R
    gross_r: dict[str, float]


def minutes(t: datetime, w) -> int:
    """Minutes after the window's index open (negative before it)."""
    return int((t - w.open).total_seconds() // 60)


def collect(symbol: str, variant: str, start: date, end: date, out: Path) -> Path:
    config = replace(
        NyIndexSweepConfig(), windows=WIDE, max_trades_per_session=99, **VARIANTS[variant]
    )
    settings = replace(RunSettings(), strategy=config)
    job = _load(DEFAULT_SOURCES, symbol, start, end, settings)
    strategy = NyIndexSweep(symbol, config, settings.detectors)
    run_backtest(strategy, job.series, settings.engine)
    m1 = next(s for s in job.series if s.timeframe is Timeframe.M1)
    decisions = [d for d in strategy.decisions if d.order is not None]
    print(f"{symbol} {variant}: {len(decisions)} entries", flush=True)
    results: dict[str, dict[datetime, tuple[float, float]]] = {}
    for name, make in EXITS.items():
        orders: dict[datetime, list[Order]] = defaultdict(list)
        for d in decisions:
            orders[d.signal.at].append(make(replace(d.order, ref=None)))
        trades = run_backtest(ReplayOrders(orders), [m1], settings.engine)
        results[name] = {t.entry_time: (t.r_net, t.r_gross) for t in trades}
    entries = []
    for d in decisions:
        s, setup = d.signal, d.signal.setup
        w = setup.window
        entries.append(
            Entry(
                symbol, variant, s.at, w.kind.value, w.trading_date, minutes(s.at, w), minutes(w.start, w),
                minutes(setup.extreme_ts, w), f"{setup.route.setup_tf.name}/{setup.route.entry_tf.name}",
                s.z3.box.kind.value, abs(s.close - d.order.stop_loss),
                {n: results[n].get(s.at, (0.0, 0.0))[0] for n in EXITS},
                {n: results[n].get(s.at, (0.0, 0.0))[1] for n in EXITS},
            )
        )  # fmt: skip
    out.mkdir(parents=True, exist_ok=True)
    path = (
        out
        / f"{symbol}_{variant.replace(' ', '_').replace('+', 'p').replace('(', '').replace(')', '')}.pkl"
    )
    path.write_bytes(pickle.dumps(entries))
    return path


# --- report --------------------------------------------------------------------------------


def pick(entries: list[Entry], before: int, after: int, kinds=("am", "pm"), first_only=True):
    """The entries a window [open - before, open + after] would have taken: the setup's
    sweep inside it, the entry inside it, the first one per window and symbol."""
    chosen, seen = [], set()
    for e in sorted(entries, key=lambda e: e.at):
        if e.window not in kinds:
            continue
        if not (-before <= e.setup_start and e.open_offset <= after):
            continue
        key = (e.symbol, e.date, e.window)
        if first_only and key in seen:
            continue
        seen.add(key)
        chosen.append(e)
    return chosen


def stats(es: list[Entry], exit_name: str) -> dict:
    r = [e.net_r[exit_name] for e in es]
    g = [e.gross_r[exit_name] for e in es]
    n = len(r)
    if not n:
        return {"n": 0}
    sd = statistics.pstdev(r) if n > 1 else 0.0
    return {
        "n": n,
        "net_R": round(sum(r), 1),
        "gross_R": round(sum(g), 1),
        "per_trade": round(sum(r) / n, 3),
        "se_total": round(sd * n**0.5, 1),
        "win_%": round(100 * sum(x > 0.05 for x in r) / n, 1),
    }


def table(rows: list[dict]) -> list[str]:
    cols = list(dict.fromkeys(k for r in rows for k in r))
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    out += ["| " + " | ".join(str(r.get(c, "")) for c in cols) + " |" for r in rows]
    return out


def report(entries: list[Entry], args) -> str:
    variants = sorted({e.variant for e in entries})
    base = [e for e in entries if e.variant == args.base_variant]
    L = ["# Strategy 2 exploration", ""]
    L += [
        (
            f"Entries: {len(entries)} over {sorted({e.symbol for e in entries})}, variants "
            f"{variants}. `se_total` = noise of the total in R (one standard error)."
        ),
        "",
        "## 1. Entry time after the open (all entries, no limit; 3 parts + BE vs TP1 only)",
    ]
    rows = []
    for kind in ("am", "pm"):
        for lo in range(-BEFORE_MAX, AFTER_MAX, 30):
            es = [e for e in base if e.window == kind and lo <= e.open_offset < lo + 30]
            for ex in ("3 parts + BE (today)", "TP1 only"):
                rows.append({"window": kind, "minutes vs open": f"{lo:+d}..{lo + 30:+d}",
                             "exit": ex, **stats(es, ex)})  # fmt: skip
    L += table(rows) + [""]
    L += ["## 2. Window size: first trade per window and index (max trades 1)", ""]
    rows = []
    for kinds in (("am",), ("pm",), ("am", "pm")):
        for before in (0, 30, 60, 90):
            for after in (60, 90, 120, 150, 180):
                es = pick(base, before, after, kinds)
                rows.append(
                    {
                        "sessions": "+".join(kinds),
                        "before": before,
                        "after": after,
                        **stats(es, "3 parts + BE (today)"),
                        "TP1 only": stats(es, "TP1 only").get("net_R"),
                    }
                )
    L += table(rows) + [""]
    L += ["## 3. Exit structure (default window 30 min before to 120 after, max trades 1)", ""]
    es = pick(base, 30, 120)
    L += table([{"exit": ex, **stats(es, ex)} for ex in EXITS]) + [""]
    L += ["## 4. Sweep rule variants x exit (same window)", ""]
    rows = []
    for v in variants:
        es = pick([e for e in entries if e.variant == v], 30, 120)
        for ex in ("3 parts + BE (today)", "TP1 only", "2R only"):
            rows.append({"sweep variant": v, "exit": ex, **stats(es, ex)})
    L += table(rows) + [""]
    L += ["## 5. Halves (is it stable?) - base variant, default window", ""]
    rows = []
    for label, a, b in (("2023-2024", 2023, 2024), ("2025-2026", 2025, 2026)):
        part = [e for e in pick(base, 30, 120) if a <= e.at.year <= b]
        for ex in ("3 parts + BE (today)", "TP1 only", "2R only"):
            rows.append({"period": label, "exit": ex, **stats(part, ex)})
    L += table(rows) + [""]
    return "\n".join(L)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("collect")
    c.add_argument("symbol", choices=["NAS100", "US500"])
    c.add_argument("--variant", default="base", choices=list(VARIANTS))
    c.add_argument("--start", type=date.fromisoformat, default=date(2023, 1, 1))
    c.add_argument("--end", type=date.fromisoformat, default=date(2026, 9, 30))
    c.add_argument("--out", type=Path, default=OUT)
    r = sub.add_parser("report")
    r.add_argument("--out", type=Path, default=OUT)
    r.add_argument("--base-variant", default="base")
    args = p.parse_args(argv)
    if args.cmd == "collect":
        print(collect(args.symbol, args.variant, args.start, args.end, args.out))
        return 0
    entries = [e for f in sorted(args.out.glob("*.pkl")) for e in pickle.loads(f.read_bytes())]
    text = report(entries, args)
    (args.out / "report.md").write_text(text, encoding="utf-8")
    print(text)
    rows = [vars(e) | {"net_r": e.net_r["3 parts + BE (today)"]} for e in entries]
    cols = [k for k in rows[0] if k not in ("net_r", "gross_r")] + ["net_r"] if rows else []
    with (args.out / "entries.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
