"""Card 2: build the wide US share universe (rule frozen in docs/share-universe.md, 5163736). Signal-free.

Steps (each resumable, data git-ignored under data/cache/):
  finra     FINRA daily short-volume files, first trading day of each month 2015-07 .. now -> data/cache/finra/daily
  symbols   candidates = FINRA symbols (^[A-Z]+(/[A-Z])?$, / -> .) + Alpaca us_equity assets on listed exchanges
  daily     Alpaca daily bars from 2015-07-01 for every candidate -> data/cache/alpaca_1d/<SYM>.csv
  universe  monthly top 1,000 by 60-session median dollar volume (close > 5, >= 60 bars, de-duplicated, no funds)
            -> data/cache/alpaca_meta/universe.csv (month, symbol, rank, dollar_volume) + audit counts
  bars30    Alpaca 30Min bars from 2015-12-01 for the union of the monthly universes -> data/cache/alpaca_30m
Run: .venv/Scripts/python.exe research/screens/2026-11-17_card2_share_universe.py finra symbols daily universe bars30
"""

import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from backtester.data import alpaca

FINRA = Path("data/cache/finra/daily")
META = Path("data/cache/alpaca_meta")
D1 = Path("data/cache/alpaca_1d")
M30 = Path("data/cache/alpaca_30m")
CNMS_FROM = "2018-08-01"
SYMBOL = re.compile(r"^[A-Z]+(/[A-Z])?$")
FUNDS = re.compile(
    r"ETF|ETN|Fund|iShares|SPDR|ProShares|Direxion|Invesco|Vanguard|VanEck|WisdomTree|Global X|First Trust|Schwab|"
    r"ARK |Ultra|Leveraged|Daily .*(Bull|Bear)|Notes|Depositary Shares .*%|Preferred|Warrant|Unit|Right",
    re.IGNORECASE,
)
LISTED = {"NYSE", "NASDAQ", "AMEX", "ARCA", "BATS"}
# A4 (2026-11-17, before any return): delisted products / non-common symbols with no Alpaca asset, found by reading
# all 532 no-asset universe members of the first build
EXCLUDE = {
        "XIV",
        "TVIX",
        "UWTI",
        "DWTI",
        "UGAZ",
        "DGAZ",
        "RSX",
        "SPLG",
        "AMJ",
        "CSJ",
        "CIU",
        "VALE.P",
        "XXXX",
    }
TOP, MIN_BARS, MIN_PRICE, WINDOW = 1000, 60, 5.0, 60


def get(url):
    """curl (FINRA's CDN refuses Python's urllib); None when the file does not exist (403 / 404)."""
    r = subprocess.run(
        ["curl", "-s", "-w", "\n%{http_code}", url], capture_output=True, timeout=120, check=True
    )
    body, _, code = r.stdout.rpartition(b"\n")
    if code in (b"403", b"404"):
        return None
    if code != b"200":
        raise RuntimeError(f"FINRA HTTP {code.decode()} for {url}")
    return body


def finra():
    FINRA.mkdir(parents=True, exist_ok=True)
    for month in pd.period_range("2015-07", pd.Timestamp.now().strftime("%Y-%m"), freq="M"):
        for day in pd.bdate_range(month.start_time, month.start_time + pd.Timedelta(days=7)):
            ds = day.strftime("%Y%m%d")
            feeds = ["CNMS"] if day >= pd.Timestamp(CNMS_FROM) else ["FNSQ", "FNYX", "FNRA"]
            got = 0
            for f in feeds:
                path = FINRA / f"{f}shvol{ds}.txt"
                if path.exists():
                    got += 1
                    continue
                body = get(f"https://cdn.finra.org/equity/regsho/daily/{f}shvol{ds}.txt")
                if body:
                    path.write_bytes(body)
                    got += 1
            if got:
                print(f"finra {month}: {ds} ({got} files)", flush=True)
                break


def finra_symbols():
    """{month 'YYYY-MM': set of symbols in Alpaca form}."""
    out = {}
    for p in sorted(FINRA.glob("*.txt")):
        d = pd.read_csv(p, sep="|", usecols=["Symbol"], dtype=str).Symbol.dropna()
        month = f"{p.stem[-8:-4]}-{p.stem[-4:-2]}"
        keep = {s.replace("/", ".") for s in d if SYMBOL.match(s)}
        out.setdefault(month, set()).update(keep)
    return out


def assets():
    a = []
    for st in ("active", "inactive"):
        a += json.loads((META / f"assets_{st}.json").read_text())
    return {x["symbol"]: x for x in a if x["exchange"] in LISTED}


def symbols():
    fs = finra_symbols()
    cand = set().union(*fs.values()) | set(assets())
    cand = sorted(s for s in cand if re.match(r"^[A-Z]+(\.[A-Z])?$", s))
    (META / "candidates.txt").write_text("\n".join(cand) + "\n")
    print(
        f"candidates {len(cand)} (FINRA months {len(fs)}, FINRA symbols {len(set().union(*fs.values()))})"
    )


def daily():
    cand = (META / "candidates.txt").read_text().split()
    alpaca.download_batch(
        cand, "1Day", "2015-07-01", alpaca.http_fetch(*alpaca.keys()), D1, batch=100
    )


def load_daily():
    rows = []
    for p in D1.glob("*.csv"):
        if p.stat().st_size < 60:
            continue
        d = pd.read_csv(p, usecols=["ts", "close", "volume"])
        d["symbol"] = p.stem
        rows.append(d)
    d = pd.concat(rows, ignore_index=True)
    d["day"] = (
        pd.to_datetime(d.ts, utc=True)
        .dt.tz_convert("America/New_York")
        .dt.tz_localize(None)
        .dt.normalize()
    )
    return d.drop(columns="ts")


def universe():
    fs = finra_symbols()
    meta = assets()
    funds = {
        s
        for s, x in meta.items()
        if x["exchange"] in ("ARCA", "BATS") or FUNDS.search(x.get("name") or "")
    } | EXCLUDE
    d = load_daily()
    d = d[~d.symbol.isin(funds)]
    # de-duplicate: same close and volume on a day = one security; prefer the symbol in that month's FINRA list
    d["month"] = d.day.dt.strftime("%Y-%m")
    d["in_finra"] = [s in fs.get(m, ()) for s, m in zip(d.symbol, d.month, strict=True)]
    d = d.sort_values(
        ["day", "close", "volume", "in_finra", "symbol"], ascending=[True, True, True, False, True]
    )
    dup = d.duplicated(["day", "close", "volume"])
    print(
        f"daily rows {len(d)}, duplicate security-days dropped {int(dup.sum())}, fund symbols excluded {len(funds)}"
    )
    d = d[~dup]
    d["dv"] = d.close * d.volume
    wide_dv = d.pivot(index="day", columns="symbol", values="dv").sort_index()
    wide_c = d.pivot(index="day", columns="symbol", values="close").reindex(wide_dv.index)
    month_end = wide_dv.groupby(wide_dv.index.to_period("M")).apply(lambda x: x.index.max())
    out = []
    for per, last in month_end.items():
        nxt = (per + 1).strftime("%Y-%m")
        if nxt < "2016-01":
            continue
        hist = wide_dv.loc[:last]
        n = hist.notna().sum()
        med = hist.iloc[-WINDOW:].median()
        ok = (n >= MIN_BARS) & (wide_c.loc[last] > MIN_PRICE) & med.notna()
        r = med[ok].reset_index()
        r.columns = ["symbol", "dv"]
        r = r.sort_values(["dv", "symbol"], ascending=[False, True]).head(TOP)
        r["month"], r["rank"] = nxt, np.arange(1, len(r) + 1)
        out.append(r)
    u = pd.concat(out)[["month", "symbol", "rank", "dv"]]
    u.to_csv(META / "universe.csv", index=False)
    by = u.groupby("month")
    print(
        f"universe months {u.month.nunique()} ({u.month.min()} .. {u.month.max()}), union {u.symbol.nunique()} symbols"
    )
    print("members per month min / median:", by.size().min(), int(by.size().median()))
    print(
        "rank-1000 median dollar volume (USD M) by year:",
        (by.dv.min().groupby(lambda m: m[:4]).median() / 1e6).round(1).to_dict(),
    )
    big = u[u.dv >= 20e6].groupby("month").size()
    print(
        "names >= USD 20 M median dollar volume per month, median by year:",
        big.groupby(lambda m: m[:4]).median().astype(int).to_dict(),
    )
    no_meta = u[~u.symbol.isin(meta)].groupby("month").size()
    print(
        "members without an Alpaca asset (delisted before the list), median per month by year:",
        no_meta.groupby(lambda m: m[:4]).median().astype(int).to_dict() if len(no_meta) else {},
    )
    look = u[u.symbol.map(lambda s: bool(FUNDS.search((meta.get(s) or {}).get("name") or "")))]
    print(f"fund-like names left by the filter (A1 audit): {look.symbol.nunique()}")


def bars30():
    syms = sorted(pd.read_csv(META / "universe.csv").symbol.unique())
    alpaca.download_batch(
        syms, "30Min", "2015-12-01", alpaca.http_fetch(*alpaca.keys()), M30, batch=20
    )


if __name__ == "__main__":
    steps = {
        "finra": finra,
        "symbols": symbols,
        "daily": daily,
        "universe": universe,
        "bars30": bars30,
    }
    for a in sys.argv[1:]:
        steps[a]()
