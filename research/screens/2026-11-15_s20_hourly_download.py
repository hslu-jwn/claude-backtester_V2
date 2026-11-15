"""Download Binance USDT-M 1 h klines (monthly archives, data.binance.vision, public) for every member of the
top-100 Strategy 20 book on any weekday anchor in the test period, 2023-12..2026-10, into data/cache/binance_1h
(ignored). Used by the hourly prop check. Run: .venv/Scripts/python.exe research/screens/2026-11-15_s20_hourly_download.py
"""
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

import pandas as pd

from backtester.tools import crypto_flow as cf

OUT = Path("data/cache/binance_1h")


def members():
    k0, f0 = cf.load()
    syms = set()
    for sh in range(7):
        dt = pd.Timedelta(days=sh)
        kk = {s: d.set_axis(d.index - dt) for s, d in k0.items()}
        ff = {s: (f.set_axis(f.index - dt) if f is not None else None) for s, f in f0.items()}
        _, legs = cf.compute_weeks(kk, ff, date(2023, 12, 25), date(2026, 10, 31), cf.LIQUID)
        syms |= {r["symbol"] for r in legs}
    return sorted(syms)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    months = pd.period_range("2023-12", "2026-10", freq="M")
    syms = members()
    print(len(syms), "symbols")
    got = miss = 0
    for s in syms:
        for m in months:
            name = f"{s}-1h-{m}.zip"
            p = OUT / name
            if p.exists():
                continue
            url = f"https://data.binance.vision/data/futures/um/monthly/klines/{s}/1h/{name}"
            try:
                urllib.request.urlretrieve(url, p)
                got += 1
            except urllib.error.HTTPError:
                miss += 1  # not listed that month
    print(f"downloaded {got}, missing {miss}")


if __name__ == "__main__":
    main()
