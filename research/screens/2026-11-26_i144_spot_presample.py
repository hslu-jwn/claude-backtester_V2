"""I-144: Strategy 20 on Binance spot 2018-01 .. 2019-12, pre-sample replication (knowledge/ideas.md › I-144).

Card registered 2026-11-26 (commit d1407b5) before any 2018-2019 data was read; downloads on the user's go (2026-11-26).
Rule = Strategy 20's frozen rules 1-4 and 6 through the I-78 screen's own functions (`week_rows`, `spread`), on a
separate root with no funding files; net = price spread - 20 bp a week.
  download  : list every spot pair in the data.binance.vision archive, keep <BASE>USDT minus the card's exclusions,
              fetch daily klines 2017-10 .. 2019-12 into data/cache/binance_spot_presample/klines_1d/
  coverage  : signal-free: eligible pairs and weeks with a book (>= 20 eligible); no return is computed
  run       : the one look (SUPPORTED net > 0 and t >= 2.0; CONTRARY net <= 0; else INCONCLUSIVE) + reported items
Run: .venv/Scripts/python.exe research/screens/2026-11-26_i144_spot_presample.py download | coverage | run
"""

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from backtester.data import binance_wide

ROOT = Path("data/cache/binance_spot_presample")
FIRST, LAST = pd.Timestamp("2018-01-01"), pd.Timestamp("2019-12-30")  # Mondays of the period
EXCLUDED = {
    "USDC",
    "TUSD",
    "PAX",
    "USDP",
    "BUSD",
    "USDS",
    "USDSB",
    "DAI",
    "EUR",
    "GBP",
    "AUD",
    "TRY",
    "RUB",
    "BRL",
    "NGN",
    "BIDR",
    "IDRT",
    "UAH",
    "ZAR",
    "BKRW",
}
LEVERAGED = ("UP", "DOWN", "BULL", "BEAR")
MIN_WEEKS = 52  # the card's coverage floor

spec = importlib.util.spec_from_file_location(
    "i78", "research/screens/2026-11-14_i78_crypto_wide_factors_screen.py"
)
i78 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(i78)
i78.END = pd.Timestamp("2019-12-31")  # no bar after the period is read


def keep(symbol):
    base = symbol[:-4]
    return symbol.endswith("USDT") and base not in EXCLUDED and not base.endswith(LEVERAGED)


def download():
    _, prefixes = binance_wide._listing("data/spot/monthly/klines/", binance_wide._fetch, "/")
    syms = sorted(s for s in (p.rstrip("/").rsplit("/", 1)[-1] for p in prefixes) if keep(s))
    print(f"{len(prefixes)} spot pairs in the archive, {len(syms)} kept", flush=True)
    (ROOT / "klines_1d").mkdir(parents=True, exist_ok=True)
    for i, s in enumerate(syms):
        binance_wide.update_spot(ROOT, [s], "2019-12", start_after="2017-09")
        if i % 100 == 0:
            print(f"{i} / {len(syms)}", flush=True)
    have = [p for p in (ROOT / "klines_1d").glob("*.csv")]
    print(f"done: {len(have)} pairs with data before 2020")


def weeks():
    k, fund = i78.load((ROOT,))
    out = {}
    for m in pd.date_range(FIRST, LAST, freq="W-MON"):
        w = i78.week_rows(k, fund, m)
        if len(w) >= i78.MIN_ELIG:
            out[m] = w
    return k, out


def coverage():
    k, w = weeks()
    n = pd.Series({m: len(x) for m, x in w.items()}, dtype=float)
    print(
        f"pairs with data: {len(k)}; weeks with a book: {len(n)} of {len(pd.date_range(FIRST, LAST, freq='W-MON'))}"
    )
    if len(n):
        print(
            f"eligible per week: median {n.median():.0f}, min {n.min():.0f}, max {n.max():.0f}; first {n.index[0]:%Y-%m-%d}"
        )
        by = n.groupby(n.index.year).agg(["count", "median"])
        print(by.to_string())
    print("enough for the look" if len(n) >= MIN_WEEKS else "PARK on power: under 52 weeks")


def run():
    _, w = weeks()
    if len(w) < MIN_WEEKS:
        sys.exit("under 52 weeks with a book: parked, no return read")
    rows = {m: i78.spread(x, "flow") for m, x in w.items()}
    price = pd.Series({m: r[1] for m, r in rows.items()})
    net = price - i78.COST_BP
    t = i78.tstat(net)
    verdict = (
        "SUPPORTED"
        if net.mean() > 0 and t >= 2.0
        else ("CONTRARY" if net.mean() <= 0 else "INCONCLUSIVE")
    )
    print(
        f"I-144: {len(net)} weeks, gross {price.mean():+.1f} bp a week, net {net.mean():+.1f}, t {t:.2f} -> {verdict}"
    )
    h = net.groupby(net.index.year).mean()
    print("halves (by year): " + ", ".join(f"{y} {v:+.1f}" for y, v in h.items()))
    capped = []
    for x in w.values():
        x = x.dropna(subset=["flow"]).sort_values(["flow", "sym"], kind="mergesort")
        n = len(x) // 5
        r = x.ret.clip(-5000, 5000)
        capped.append(r.iloc[-n:].mean() - r.iloc[:n].mean() - i78.COST_BP)
    print(f"members capped at +-50 %: net {np.mean(capped):+.1f}, t {i78.tstat(capped):.2f}")
    nb = net.drop(net.nlargest(2).index)
    print(f"without the 2 best weeks: net {nb.mean():+.1f}, t {i78.tstat(nb):.2f}")
    legs = pd.Series({m: r[2] for m, r in rows.items()})
    print(f"legs per side: median {legs.median():.0f}, min {legs.min():.0f}")
    # placebo (report only): the same sort against the return of week t-2 (before the signal window)
    prev = {m - pd.Timedelta(days=14): m for m in w}
    pl = []
    for m0, m in prev.items():
        if m0 in w:
            a = w[m].dropna(subset=["flow"]).set_index("sym").flow
            b = w[m0].set_index("sym").ret
            j = pd.concat([a, b], axis=1, keys=["flow", "ret"]).dropna().reset_index()
            j = j.rename(columns={"index": "sym"}).sort_values(["flow", "sym"], kind="mergesort")
            n = len(j) // 5
            if n:
                pl.append(j.ret.iloc[-n:].mean() - j.ret.iloc[:n].mean())
    if len(pl) > 2:
        print(
            f"placebo week t-2: gross {np.mean(pl):+.1f}, t {i78.tstat(pl):.2f} ({len(pl)} weeks)"
        )


if __name__ == "__main__":
    {"download": download, "coverage": coverage, "run": run}[sys.argv[1]]()
