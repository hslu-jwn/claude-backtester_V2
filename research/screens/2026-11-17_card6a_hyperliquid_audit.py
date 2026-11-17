"""Card 6 step A (Fable sweep 2026-11-16): Hyperliquid public-API audit, signal-free (no return, funding sign or
sort is computed).

Public `POST https://api.hyperliquid.xyz/info` (no key): `meta` (perp list, delisted flag), `candleSnapshot` 1d per
perp, `fundingHistory` per perp (first page only: when funding starts). Daily candles are cached (git-ignored) in
data/cache/hyperliquid/candles_1d/<COIN>.csv for step B. Counts: perps, history start, and the Mondays on which at
least 40 perps pass Strategy 20's liquidity rule (>= 60 daily bars before the Monday, 30-day median quote volume
>= 5 M USD; quote volume = base volume x close).
Run: .venv/Scripts/python.exe research/screens/2026-11-17_card6a_hyperliquid_audit.py
"""

import json
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

URL = "https://api.hyperliquid.xyz/info"
CACHE = Path("data/cache/hyperliquid/candles_1d")
START_MS = int(pd.Timestamp("2022-01-01", tz="UTC").timestamp() * 1000)
PAUSE = 1.0  # info weight 20 per candle request, 1,200 a minute


def post(body):
    req = urllib.request.Request(
        URL, json.dumps(body).encode(), headers={"Content-Type": "application/json"}
    )
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                time.sleep(PAUSE)
                return json.loads(r.read())
        except OSError:
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"Hyperliquid info failed: {body['type']}")


def candles(coin):
    path = CACHE / f"{coin}.csv"
    if path.exists():
        return pd.read_csv(path)
    end = int(time.time() * 1000)
    rows = post(
        {
            "type": "candleSnapshot",
            "req": {"coin": coin, "interval": "1d", "startTime": START_MS, "endTime": end},
        }
    )
    d = pd.DataFrame(rows or [], columns=["t", "o", "h", "l", "c", "v", "n"])
    path.parent.mkdir(parents=True, exist_ok=True)
    d.to_csv(path, index=False)
    return d


def main():
    uni = post({"type": "meta"})["universe"]
    out = []
    for u in uni:
        d = candles(u["name"])
        f = post({"type": "fundingHistory", "coin": u["name"], "startTime": 0})
        out.append(
            {
                "coin": u["name"],
                "delisted": bool(u.get("isDelisted")),
                "bars": len(d),
                "first": pd.to_datetime(d.t.min(), unit="ms") if len(d) else pd.NaT,
                "last": pd.to_datetime(d.t.max(), unit="ms") if len(d) else pd.NaT,
                "funding_first": pd.to_datetime(f[0]["time"], unit="ms") if f else pd.NaT,
            }
        )
    a = pd.DataFrame(out)
    print(
        f"perps {len(a)} (delisted {a.delisted.sum()}); with daily candles {(a.bars > 0).sum()} "
        f"(delisted with candles {(a.delisted & (a.bars > 0)).sum()}); first candle {a['first'].min().date()}, "
        f"first funding {a.funding_first.min()}"
    )
    print(
        "first candle by year:",
        a["first"].dt.year.value_counts().sort_index().to_dict(),
        "| delisted by last-candle year:",
        a[a.delisted]["last"].dt.year.value_counts().sort_index().to_dict(),
    )
    if (a.bars >= 5000).any():
        print("WARNING: a candle request hit 5,000 bars (history may be cut)")

    elig = {}
    for coin in a.coin[a.bars > 0]:
        d = candles(coin)
        day = pd.to_datetime(d.t, unit="ms").dt.normalize()
        q = pd.Series((d.v * d.c).to_numpy(float), index=day)
        q = q[~q.index.duplicated()]
        med = q.rolling(30).median().shift(1)  # known before the day
        n_before = pd.Series(np.arange(len(q)), index=q.index)
        ok = (med >= 5e6) & (n_before >= 60)
        elig[coin] = ok[ok.index.dayofweek == 0]
    e = pd.DataFrame(elig).fillna(False).sum(axis=1).sort_index()
    weeks40 = e[e >= 40]
    print(
        f"Mondays with >= 40 eligible: {len(weeks40)} "
        f"({weeks40.index.min().date() if len(weeks40) else '-'} .. {weeks40.index.max().date() if len(weeks40) else '-'}); "
        f"eligible median {int(e[e > 0].median())}, max {int(e.max())}"
    )
    print(
        "eligible by year (median per Monday):",
        e.groupby(e.index.year).median().astype(int).to_dict(),
    )


if __name__ == "__main__":
    main()
