"""I-145 maker-first fill model for Strategy 20's Monday rebalance (knowledge/ideas.md › I-145; rule fixed before data).

Orders = the trades Strategy 20's frozen book needs at each Monday 00:00 UTC (leave / enter / flip; a flip is one order;
members that stay are ignored). P0 = Sunday daily close. Arms: taker = first matching-aggressor trade at or after
00:00:01 + 5 bp; maker-first = limit at P0 filled by a print >= `ticks` ticks through P0 in the window (+ 2 bp), else
taker after the window. Saving = taker - maker-first per order, t clustered by Monday.

python research/screens/2026-11-26_i145_fill_model.py orders | size | download | run
"""

import argparse
import sys
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from backtester.data import binance_wide
from backtester.tools import crypto_flow

ORDERS = Path("results/i145/orders.csv")
CACHE = Path("data/cache/binance_aggtrades")
LATENCY_MS = 1000
READ_MS = 3 * 3600 * 1000
TAKER_FEE, MAKER_FEE = 5.0, 2.0
BNB_TAKER, BNB_MAKER = 4.5, 1.8
WAIT_PRIMARY, WAIT_SHORT = 60 * 60 * 1000, 15 * 60 * 1000
PREFIX = "data/futures/um/daily/aggTrades/{s}/"
NAME = "{s}-aggTrades-{d}.zip"


def mondays() -> list[date]:
    """Every Monday of 2023 and 2026-04-27 .. 2026-10-19."""
    out = []
    for first, last in ((date(2023, 1, 2), date(2023, 12, 25)), (date(2026, 4, 27), date(2026, 10, 19))):
        d = first
        while d <= last:
            out.append(d)
            d += timedelta(days=7)
    return out


def books(legs: list[dict]) -> dict[date, dict[str, int]]:
    """week -> {symbol: +1 long / -1 short} from compute_weeks legs."""
    out: dict[date, dict[str, int]] = {}
    for leg in legs:
        out.setdefault(pd.Timestamp(leg["week"]).date(), {})[leg["symbol"]] = 1 if leg["side"] == "long" else -1
    return out


def derive_orders(prev: dict[str, int], cur: dict[str, int]) -> dict[str, int]:
    """Monday orders: side = sign of the change in position (+1 buy, -1 sell); a flip is one order."""
    out = {}
    for s in prev.keys() | cur.keys():
        change = cur.get(s, 0) - prev.get(s, 0)
        if change:
            out[s] = int(np.sign(change))
    return out


def tick_of(prices: pd.Series) -> float:
    """Smallest positive price step among the given trades (NaN if there is none)."""
    steps = np.diff(np.unique(prices.to_numpy(dtype=float)))
    steps = steps[steps > 0]
    return round(float(steps.min()), 12) if len(steps) else float("nan")


def slip_bp(side: int, fill: float, p0: float) -> float:
    """Cost of a fill against P0 in bp before fees: a buy above or a sell below P0 costs."""
    return side * (fill - p0) / p0 * 1e4


def first_match(t: pd.DataFrame, side: int, after_ms: int) -> float:
    """First trade at or after `after_ms` whose aggressor is on our side (buy: is_buyer_maker False)."""
    m = t[(t.transact_time >= after_ms) & (t.is_buyer_maker == (side < 0))]
    return float(m.price.iloc[0]) if len(m) else float("nan")


def fill_order(t, side, p0, t0_ms, wait_ms, ticks, tick):
    """(taker slip bp, maker-first slip bp, filled) without fees; maker fill = limit at P0 = slip 0."""
    start = t0_ms + LATENCY_MS
    taker = slip_bp(side, first_match(t, side, start), p0)
    win = t[(t.transact_time >= start) & (t.transact_time < t0_ms + wait_ms)]
    eps = tick * 1e-6
    through = win.price <= p0 - ticks * tick + eps if side > 0 else win.price >= p0 + ticks * tick - eps
    if through.any():
        return taker, 0.0, True
    return taker, slip_bp(side, first_match(t, side, t0_ms + wait_ms), p0), False


def read_trades(path, t0_ms: int) -> pd.DataFrame:
    """price, transact_time, is_buyer_maker of the first 3 h after t0, read in chunks."""
    parts = []
    for chunk in pd.read_csv(path, usecols=["price", "transact_time", "is_buyer_maker"], chunksize=1_000_000):
        parts.append(chunk[chunk.transact_time < t0_ms + READ_MS])
        if chunk.transact_time.min() >= t0_ms + READ_MS:
            break
    return pd.concat(parts).sort_values("transact_time", kind="mergesort").reset_index(drop=True)


def clustered(r: pd.DataFrame) -> tuple[float, float]:
    """Mean of the per-Monday means of `saving` and its t (mean / se over Mondays)."""
    by = r.groupby("monday").saving.mean()
    return float(by.mean()), float(by.mean() / (by.std(ddof=1) / np.sqrt(len(by))))


def ts_ms(d: date) -> int:
    return int(pd.Timestamp(d, tz="UTC").timestamp() * 1000)


def cmd_orders() -> None:
    klines, funding = crypto_flow.load()
    _, legs = crypto_flow.compute_weeks(klines, funding, date(2022, 12, 26), date(2026, 10, 25))
    book = books(legs)
    rows = []
    for mon in mondays():
        prev, cur = book.get(mon - timedelta(days=7)), book.get(mon)
        if prev is None or cur is None:
            print(f"skip {mon}: no book for it or the week before")
            continue
        ts = pd.Timestamp(mon, tz="UTC")
        for s, side in sorted(derive_orders(prev, cur).items()):
            k = klines[s]
            sun = k.loc[k.index == ts - pd.Timedelta(days=1)]
            if sun.empty:
                print(f"skip {s} {mon}: no Sunday close")
                continue
            rows.append(
                {
                    "monday": mon,
                    "symbol": s,
                    "side": side,
                    "p0": float(sun.close.iloc[0]),
                    "qvol30": float(k.loc[k.index < ts].quote_volume.iloc[-30:].median()),
                }
            )
    ORDERS.parent.mkdir(parents=True, exist_ok=True)
    out = pd.DataFrame(rows)
    out.to_csv(ORDERS, index=False)
    print(f"{len(out)} orders on {out.monday.nunique()} Mondays, {out.symbol.nunique()} symbols -> {ORDERS}")


def plan() -> tuple[dict, list]:
    """{(symbol, monday): (key, size bytes)} for files in the archive, and the (symbol, monday) pairs missing there."""
    orders = pd.read_csv(ORDERS)
    found, missing = {}, []
    for s, g in orders.groupby("symbol"):
        pages = []

        def fetch(url, params=None, pages=pages):
            pages.append(binance_wide._fetch(url, params))
            return pages[-1]

        keys, _ = binance_wide._listing(PREFIX.format(s=s), fetch)
        sizes = {}
        for page in pages:
            for c in ET.fromstring(page).iter():
                if c.tag.rsplit("}", 1)[-1] == "Contents":
                    kv = {n.tag.rsplit("}", 1)[-1]: n.text for n in c}
                    sizes[kv["Key"]] = int(kv["Size"])
        for mon in sorted(set(g.monday)):
            key = PREFIX.format(s=s) + NAME.format(s=s, d=mon)
            if key in keys:
                found[(s, mon)] = (key, sizes.get(key, 0))
            else:
                missing.append((s, mon))
    return found, missing


def cmd_size() -> None:
    found, missing = plan()
    todo = {k: v for k, v in found.items() if not (CACHE / NAME.format(s=k[0], d=k[1])).exists()}
    print(
        f"files in the archive {len(found)} ({sum(v[1] for v in found.values()) / 1e9:.2f} GB), "
        f"still to download {len(todo)} ({sum(v[1] for v in todo.values()) / 1e9:.2f} GB), missing {len(missing)}"
    )
    for s, mon in missing[:20]:
        print("missing", s, mon)


def cmd_download() -> None:
    found, missing = plan()
    CACHE.mkdir(parents=True, exist_ok=True)
    n = 0
    for (s, mon), (key, _) in sorted(found.items()):
        path = CACHE / NAME.format(s=s, d=mon)
        if path.exists():
            continue
        part = path.with_suffix(".part")
        part.write_bytes(binance_wide._fetch(binance_wide.CDN + key))
        part.replace(path)
        n += 1
        if n % 100 == 0:
            print(f"{n} files downloaded", flush=True)
    print(f"downloaded {n}, missing in archive {len(missing)}")


def cmd_run() -> None:
    orders = pd.read_csv(ORDERS, parse_dates=["monday"])
    orders["monday"] = orders.monday.dt.date
    rows = []
    for mon, g in orders.groupby("monday"):
        t0 = ts_ms(mon)
        for o in g.itertuples():
            path = CACHE / NAME.format(s=o.symbol, d=mon)
            if not path.exists():
                continue
            t = read_trades(path, t0)
            tick = tick_of(t.price)
            if t.empty or np.isnan(tick):
                continue
            row = {"monday": mon, "symbol": o.symbol, "side": o.side, "qvol30": o.qvol30}
            for name, wait, ticks in (("60", WAIT_PRIMARY, 1), ("60x2", WAIT_PRIMARY, 2), ("15", WAIT_SHORT, 1)):
                tk, mk, filled = fill_order(t, o.side, o.p0, t0, wait, ticks, tick)
                row["taker"] = tk
                row[f"maker{name}"], row[f"filled{name}"] = mk, filled
            rows.append(row)
    r = pd.DataFrame(rows).dropna(subset=["taker"])
    print(f"{len(r)} of {len(orders)} orders have data")

    def arm(name, taker_fee=TAKER_FEE, maker_fee=MAKER_FEE):
        d = r.copy()
        d["saving"] = (d.taker + taker_fee) - np.where(d[f"filled{name}"], maker_fee, d[f"maker{name}"] + taker_fee)
        return d.dropna(subset=["saving"])

    primary = arm("60")
    mean, t = clustered(primary)
    two = arm("60x2")
    third = primary[primary.qvol30 <= primary.qvol30.quantile(1 / 3)]
    print(f"60 min, 1 tick: saving {mean:+.2f} bp an order, t {t:.2f} over {primary.monday.nunique()} Mondays, "
          f"fill rate {100 * primary.filled60.mean():.0f} %")
    print(f"unfilled orders: maker-first cost {primary[~primary.filled60].maker60.add(TAKER_FEE).mean():.1f} bp "
          f"vs taker {primary[~primary.filled60].taker.add(TAKER_FEE).mean():.1f} bp")
    print(f"60 min, 2 ticks: saving {clustered(two)[0]:+.2f} bp, fill rate {100 * two.filled60x2.mean():.0f} %")
    s15 = arm("15")
    print(f"15 min, 1 tick: saving {clustered(s15)[0]:+.2f} bp, t {clustered(s15)[1]:.2f}, "
          f"fill rate {100 * s15.filled15.mean():.0f} %")
    print(f"least liquid third (n {len(third)}): saving {clustered(third)[0]:+.2f} bp")
    for label, sel in (("2023", primary.monday.map(lambda d: d.year == 2023)), ("2026", primary.monday.map(lambda d: d.year == 2026))):
        sub = primary[sel]
        if len(sub):
            print(f"{label}: saving {clustered(sub)[0]:+.2f} bp, {len(sub)} orders")
    bnb = arm("60", BNB_TAKER, BNB_MAKER)
    print(f"BNB fees (taker 4.5 / maker 1.8): saving {clustered(bnb)[0]:+.2f} bp, t {clustered(bnb)[1]:.2f}")
    ok = mean >= 1.5 and t >= 2.0 and clustered(two)[0] > 0 and clustered(third)[0] > 0
    print("decision:", "ADOPT 60-minute maker-first" if ok else "keep taker")


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("cmd", choices=("orders", "size", "download", "run"))
    {"orders": cmd_orders, "size": cmd_size, "download": cmd_download, "run": cmd_run}[p.parse_args(argv).cmd]()


if __name__ == "__main__":
    main(sys.argv[1:])
