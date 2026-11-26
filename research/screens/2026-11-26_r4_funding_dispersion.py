"""R4 (lead-review intake 2026-11-26): cross-coin funding dispersion by half-year, signal only, no returns.

Is the carry premium Strategy 19 sorts on shrinking across coins, or only its level? Each Monday 00:00 UTC up to the
forward start (2026-11-16, excluded), per perp with >= 21 settled rates in the last 30 days: the 7-day funding sum in
(Monday - 7 d, Monday] (Strategy 19's signal, docs/strategy-crypto_carry.md › Rule 1), in bp. Reported per half-year:
S19's 17-coin universe top-4 minus bottom-4 signal; the wide universe (every Binance USDT perp) top-minus-bottom
quintile, cross-sectional sd and the mean level. Descriptive: no outcome, no gate.
Run: .venv/Scripts/python.exe research/screens/2026-11-26_r4_funding_dispersion.py
"""

import numpy as np
import pandas as pd

from backtester.data import binance_wide

S19 = [
    "BTC",
    "ETH",
    "BCH",
    "XRP",
    "EOS",
    "LTC",
    "TRX",
    "ETC",
    "LINK",
    "XLM",
    "ADA",
    "BNB",
    "XTZ",
    "XMR",
    "NEO",
    "DASH",
    "ATOM",
]
END = pd.Timestamp("2026-11-16", tz="UTC")  # Strategy 19's forward start: not read


def signals():
    mondays = pd.date_range(
        pd.Timestamp("2020-01-06", tz="UTC"), END - pd.Timedelta(days=1), freq="W-MON"
    )
    out = {}
    for sym in binance_wide.symbols():
        f = binance_wide.read_funding(sym)
        if f.empty:
            continue
        c = np.concatenate([[0.0], f.cumsum().to_numpy()])
        # settlements at or before each Monday, Monday - 7 d, Monday - 30 d
        now, wk, mo = (
            np.searchsorted(f.index, mondays - pd.Timedelta(days=d), side="right")
            for d in (0, 7, 30)
        )
        sig = pd.Series(1e4 * (c[now] - c[wk]), index=mondays)
        out[sym] = sig[(now - mo) >= 21]
    return pd.DataFrame(out)


def spread(row, k):
    x = row.dropna().sort_values()
    return x.iloc[-k:].mean() - x.iloc[:k].mean() if len(x) >= 2 * k else float("nan")


def main():
    s = signals()
    s19 = s[[f"{c}USDT" for c in S19 if f"{c}USDT" in s]]
    t = pd.DataFrame(
        {
            "s19_top4_bot4": s19.apply(lambda r: spread(r, 4), axis=1),
            "wide_q5_q1": s.apply(lambda r: spread(r, r.notna().sum() // 5), axis=1),
            "wide_sd": s.std(axis=1),
            "wide_level": s.mean(axis=1),
            "wide_n": s.notna().sum(axis=1),
        }
    )
    half = t.index.year.astype(str) + "H" + ((t.index.month > 6) + 1).astype(str)
    print("bp per 7 days (signal: trailing 7-day funding sum), mean over Mondays")
    print(t.groupby(half).agg(["mean"]).round(1).to_string())


if __name__ == "__main__":
    main()
