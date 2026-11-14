"""Power budget map (Fable directions row 5, 2026-11-14): the smallest effect per event each FTMO symbol x hold x
event frequency could show at t 3 on development data, against its round-trip cost. Signal-free: returns from a
fixed clock entry on every weekday, no rule.

Entry at the close of the M1 bar opening 13:00 UTC (London and New York both open; Asian indices are closed then,
their numbers describe a non-session hold), exit at the close of the first bar at or after entry + hold. sd of the
return in bp over 2015-01-01 .. 2021-09-13 (each symbol's cached days). MDE(t 3) = 3 sd / sqrt(N) with N events in
6.7 years: daily 1,700, weekly 350, monthly 80, quarterly-plus (8 a year) 54. Cost = the engine's round trip at the
entry (spread via fill_spread_time + 2 x slippage + commission), median over events, in bp. Swap is excluded (multi-
night holds pay it on top). Run: .venv/Scripts/python.exe research/screens/2026-11-14_power_budget_map.py
"""
import sys
from datetime import UTC, date, datetime
from pathlib import Path

import numpy as np

from backtester.data.sources import DEFAULT_SOURCES
from backtester.engine.costs import CostConfig, fill_spread_time
from backtester.tools.entry_screen import load_m1

START, END = date(2015, 1, 1), date(2021, 9, 13)
HOLDS = {"30m": 1800, "1h": 3600, "6h": 21600, "1d": 86400, "5d": 5 * 86400}
FREQ = {"daily": 1700, "weekly": 350, "monthly": 80, "8/yr": 54}
cfg = CostConfig()


def symbol_rows(sym):
    d = load_m1(sym, DEFAULT_SOURCES, START, END)
    t, c = d.open_s, d.close
    days = np.unique((t // 86400) * 86400)
    entries = days + 13 * 3600
    entries = entries[[datetime.fromtimestamp(x, UTC).weekday() < 5 for x in entries]]
    i = np.searchsorted(t, entries)
    ok = (i < len(t)) & (t[np.minimum(i, len(t) - 1)] == entries)
    i, entries = i[ok], entries[ok]
    p0 = c[i]
    costs = []
    for x, p in zip(entries[::20], p0[::20], strict=True):  # every 20th event is enough for a median
        at = datetime.fromtimestamp(x, UTC)
        rt = cfg.spread(sym, fill_spread_time(at), p) + 2 * cfg.slippage(sym, p) + cfg.commission_price(sym, p)
        costs.append(rt / p * 1e4)
    out = {"symbol": sym, "events": len(i), "cost_bp": float(np.median(costs)) if costs else float("nan")}
    for name, h in HOLDS.items():
        j = np.searchsorted(t, entries + h)
        good = j < len(t)
        good &= (t[np.minimum(j, len(t) - 1)] - (entries + h)) < 3600  # exit within an hour of the target time
        r = (c[np.minimum(j, len(t) - 1)][good] / p0[good] - 1) * 1e4
        out[name] = float(np.std(r)) if len(r) > 100 else float("nan")
    return out


def main(argv):
    syms = argv or sorted(p.name for p in Path("data/cache/mt5").iterdir() if p.is_dir() and not p.name.startswith("_"))
    rows = []
    for s in syms:
        try:
            rows.append(symbol_rows(s))
        except (SystemExit, KeyError, ValueError) as e:
            print(s, "skipped:", e, flush=True)
            continue
        print(rows[-1], flush=True)
    lines = ["| symbol | cost bp | " + " | ".join(f"sd {h}" for h in HOLDS) + " | MDE t3 bp: daily 1h / daily 6h / "
             "weekly 1d / weekly 5d / monthly 1d / monthly 5d / 8 a yr 1h |", "|" + "---|" * (3 + len(HOLDS))]
    for r in rows:
        def m(h, f, r=r):
            return 3 * r[h] / np.sqrt(FREQ[f])
        mde = " / ".join(f"{m(h, f):.0f}" for h, f in (("1h", "daily"), ("6h", "daily"), ("1d", "weekly"),
                                                     ("5d", "weekly"), ("1d", "monthly"), ("5d", "monthly"), ("1h", "8/yr")))
        lines.append(f"| {r['symbol']} | {r['cost_bp']:.1f} | " + " | ".join(f"{r[h]:.0f}" for h in HOLDS) + f" | {mde} |")
    out = Path("results/power_budget_map.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
