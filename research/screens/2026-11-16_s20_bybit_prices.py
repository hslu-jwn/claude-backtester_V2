"""Strategy 20 top-100 book with Bybit prices and Bybit funding (2026-11-16; diagnostic on the spent test period).

Closes the gap noted in the Bybit-universe diagnostic: the prop firms trade on Bybit, the signal comes from Binance.
Signal, eligibility and the top-100 cut use Binance volume / taker volume (unchanged); each Binance perp listed on
Bybit today (cached instrument list) gets Bybit's daily open / close (public v5 kline) and Bybit's funding history
(v5 funding/history) from its first Bybit bar; perps not on Bybit are dropped (cannot be traded there). Downloads
are cached in data/cache/bybit (ignored). Compared with the same book on Binance prices for the same coins.
Run: .venv/Scripts/python.exe research/screens/2026-11-16_s20_bybit_prices.py [--dev]  (--dev: 2020-2023, cache data/cache/bybit/dev)
"""
import json
import re
import sys
import time
import urllib.request
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from backtester.tools import crypto_flow as cf

ROOT = Path("data/cache/bybit")
DEV = "--dev" in sys.argv  # development period 2020-2023 instead of the test period
START, END = (date(2020, 1, 1), date(2023, 12, 31)) if DEV else (date(2024, 1, 1), date(2026, 10, 31))
T0 = int(pd.Timestamp("2019-09-01" if DEV else "2023-09-01", tz="UTC").timestamp() * 1000)
T1 = int(pd.Timestamp("2024-01-02" if DEV else "2026-11-02", tz="UTC").timestamp() * 1000)
SUB = "dev" if DEV else ""


def base(s):
    return re.sub(r"^(1000000|100000|10000|1000|1M)|1000$", "", re.sub(r"USDT$", "", s))


def get(url):
    for _ in range(5):
        try:
            d = json.loads(urllib.request.urlopen(url, timeout=30).read().decode("utf-8"))
            if d.get("retCode") == 0:
                return d["result"]["list"]
        except OSError:
            pass
        time.sleep(1.0)
    raise RuntimeError(url)


def klines(sym):
    p = ROOT / SUB / "klines_1d" / f"{sym}.csv"
    if not p.exists():
        rows, end = [], T1
        while True:
            lst = get(f"https://api.bybit.com/v5/market/kline?category=linear&symbol={sym}&interval=D&start={T0}&end={end}&limit=1000")
            rows += lst
            if len(lst) < 1000:
                break
            end = int(lst[-1][0]) - 1
            if end <= T0:
                break
            time.sleep(0.05)
        p.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(rows, columns=["t", "open", "high", "low", "close", "volume", "turnover"]).to_csv(p, index=False)
    d = pd.read_csv(p)
    d.index = pd.to_datetime(d.t.astype("int64"), unit="ms", utc=True)
    return d[~d.index.duplicated()].sort_index()


def funding(sym):
    p = ROOT / SUB / "funding" / f"{sym}.csv"
    if not p.exists():
        rows, end = [], T1
        while True:
            lst = get(f"https://api.bybit.com/v5/market/funding/history?category=linear&symbol={sym}&startTime={T0}&endTime={end}&limit=200")
            rows += lst
            if len(lst) < 200:
                break
            end = int(lst[-1]["fundingRateTimestamp"]) - 1
            if end <= T0:  # last page reached the window start: an empty range is an API error
                break
            time.sleep(0.05)
        p.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(rows).to_csv(p, index=False)
    d = pd.read_csv(p)
    if d.empty:
        return pd.Series(dtype=float, index=pd.DatetimeIndex([], tz="UTC"))
    s = pd.Series(d.fundingRate.to_numpy(float), index=pd.DatetimeIndex(pd.to_datetime(d.fundingRateTimestamp.astype("int64"), unit="ms", utc=True)).floor("min"))
    return s[~s.index.duplicated()].sort_index()


def stats(name, tr):
    n = np.array([t["net_bp"] for t in tr])
    print(f"{name}: {len(n)} weeks, net {n.mean():+.1f} bp/week, t {n.mean() / n.std(ddof=1) * np.sqrt(len(n)):.2f}, worst {n.min():+.0f}")


def main():
    inst = json.loads((ROOT / "linear_instruments_2026-11-15.json").read_text(encoding="utf-8"))
    on_bybit = {}
    for x in inst:
        if x["type"] == "LinearPerpetual" and x["symbol"].endswith("USDT"):
            on_bybit.setdefault(base(x["symbol"]), x["symbol"])
    k, f = cf.load()
    kb, fb, kn, fn = {}, {}, {}, {}
    for s, d in k.items():
        b = on_bybit.get(base(s))
        if b is None or d.index.max() < pd.Timestamp(START, tz="UTC"):
            continue
        by = klines(b)
        if by.empty:
            continue
        j = d.join(by[["open", "close"]], rsuffix="_by", how="inner")
        if j.empty:
            continue
        kn[s], fn[s] = d.loc[j.index], f.get(s)  # same coins and days, Binance prices
        j["open"], j["close"] = j.open_by, j.close_by
        kb[s], fb[s] = j[list(d.columns)], funding(b)
    print(f"{len(kb)} Binance perps traded on Bybit (with Bybit bars in the window)")
    stats("top-100 book, Binance prices, same coins", cf.compute_weeks(kn, fn, START, END, cf.LIQUID)[0])
    stats("top-100 book, Bybit prices + Bybit funding", cf.compute_weeks(kb, fb, START, END, cf.LIQUID)[0])


if __name__ == "__main__":
    main()
