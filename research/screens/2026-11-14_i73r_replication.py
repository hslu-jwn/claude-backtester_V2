"""I-73R: the frozen I-73 rule on 20 unseen perps (knowledge/ideas.md › I-73, replication).

Pre-registered in ba253bc before the data was downloaded. Weeks 2021-09-20 .. 2026-10-25.
Pass: net mean > 0; t >= 2.0; both halves > 0; net > 0 without the 2 best weeks.
`--power`: signal-free weekly sd of random 4-vs-4 books (recorded before the run).
Run: .venv/Scripts/python.exe research/screens/2026-11-14_i73r_replication.py [--power]
"""

import importlib.util
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from backtester.data.sources import BINANCE_CACHE_DIR, SymbolSources
from backtester.strategy.crypto_carry.book import DEFAULT, CryptoCarryConfig
from backtester.tools.crypto_carry import compute_weeks, read_funding

R20 = tuple(
    s + "USDT"
    for s in (
        [
            "BAT",
            "IOST",
            "IOTA",
            "ONT",
            "QTUM",
            "VET",
            "ZEC",
            "THETA",
            "ALGO",
            "COMP",
            "KNC",
            "ZIL",
            "ZRX",
            "BAND",
            "DOGE",
            "KAVA",
            "OMG",
            "RLC",
            "SXP",
            "DOT",
        ]
    )
)
START, END = date(2021, 9, 20), date(2026, 10, 25)


def book(symbols):
    cfg = CryptoCarryConfig(symbols=symbols)
    trades, _, skipped = compute_weeks(
        read_funding(symbols), SymbolSources.single(BINANCE_CACHE_DIR, symbols), START, END, cfg
    )
    return pd.DataFrame(trades).set_index("entry_time"), skipped


def tstat(x):
    return x.mean() / x.std(ddof=1) * np.sqrt(len(x))


if __name__ == "__main__":
    if "--power" in sys.argv:
        spec = importlib.util.spec_from_file_location(
            "s", Path(__file__).with_name("2026-11-13_i73_crypto_carry_xs_screen.py")
        )
        s = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(s)
        s.SYMBOLS = list(R20)
        s.power(s.weeks(s.TEST_START, s.TEST_END + pd.Timedelta(days=6)))
        sys.exit()
    d, skipped = book(R20)
    half, drop2 = len(d) // 2, d.net_bp.drop(d.net_bp.nlargest(2).index)
    print(
        f"R20 weeks {len(d)} ({d.index[0].date()} .. {d.index[-1].date()}), skipped {len(skipped)}"
    )
    print(
        f"net {d.net_bp.mean():+.1f} bp/week  t {tstat(d.net_bp):+.2f}  price {d.price_bp.mean():+.1f}  funding {d.funding_bp.mean():+.1f}"
        f"  win {np.mean(d.net_bp > 0):.2f}  sd {d.net_bp.std():.0f}  worst {d.net_bp.min():+.0f}"
    )
    print(
        f"halves {d.net_bp.iloc[:half].mean():+.1f} / {d.net_bp.iloc[half:].mean():+.1f}  without 2 best {drop2.mean():+.1f}"
    )
    gates = {
        "net > 0": d.net_bp.mean() > 0,
        "t >= 2.0": tstat(d.net_bp) >= 2.0,
        "both halves > 0": d.net_bp.iloc[:half].mean() > 0 and d.net_bp.iloc[half:].mean() > 0,
        "without 2 best > 0": drop2.mean() > 0,
    }
    print(
        "gates:",
        {k: bool(v) for k, v in gates.items()},
        "->",
        "PASSED" if all(gates.values()) else "FAILED",
    )
    print(d.groupby(d.index.year)[["net_bp", "price_bp", "funding_bp"]].mean().round(1).to_string())
    u, _ = book(DEFAULT.symbols + R20)
    print(
        f"diagnostic, 37-symbol union: weeks {len(u)} net {u.net_bp.mean():+.1f} t {tstat(u.net_bp):+.2f}"
    )
