"""I-106 insider open-market purchases on the wide US share universe (rule fixed in knowledge/ideas.md, 6f9c9b0).

SEC Insider Transactions Data Sets 2016Q1 .. 2021Q3 (data/cache/sec_insider, user's contact string), Alpaca daily
closes, universe docs/share-universe.md. Development only: holds that end by 2021-09-13.
Steps: download, power (signal-free), run.
Run: .venv/Scripts/python.exe research/screens/2026-11-17_i106_insider_buys_screen.py download | power | run
"""

import io
import subprocess
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

SEC = Path("data/cache/sec_insider")
D1 = Path("data/cache/alpaca_1d")
UNIVERSE = Path("data/cache/alpaca_meta/universe.csv")
QUARTERS = [f"{y}q{q}" for y in range(2016, 2022) for q in range(1, 5)][:23]  # 2016q1 .. 2021q3
START, END = pd.Timestamp("2016-04-01"), pd.Timestamp("2021-09-13")
HOLD, COST, MIN_VALUE = 20, 8.0, 25_000.0


def download():
    import keyring

    ua = f"backtester-research {keyring.get_password('backtester-contact', 'email')}"
    SEC.mkdir(parents=True, exist_ok=True)
    for q in QUARTERS:
        path = SEC / f"{q}_form345.zip"
        if path.exists():
            continue
        url = f"https://www.sec.gov/files/structureddata/data/insider-transactions-data-sets/{q}_form345.zip"
        r = subprocess.run(
            ["curl", "-s", "-A", ua, "-w", "\n%{http_code}", url],
            check=False,
            capture_output=True,
            timeout=600,
        )
        body, _, code = r.stdout.rpartition(b"\n")
        if code != b"200":
            raise RuntimeError(f"SEC HTTP {code.decode()} for {q}")
        path.write_bytes(body)
        print(f"{q}: {len(body) / 1e6:.1f} MB", flush=True)


def table(z, name, cols):
    return pd.read_csv(
        z.open(name), sep="\t", usecols=cols, dtype=str, quoting=3, on_bad_lines="skip"
    )


def filings(code, min_value):
    """Officer / director Form 4 transactions with `code` (P buys, S sales): one row per (symbol, filing date)."""
    rows = []
    for q in QUARTERS:
        z = zipfile.ZipFile(io.BytesIO((SEC / f"{q}_form345.zip").read_bytes()))
        sub = table(
            z,
            "SUBMISSION.tsv",
            ["ACCESSION_NUMBER", "FILING_DATE", "DOCUMENT_TYPE", "ISSUERTRADINGSYMBOL"],
        )
        own = table(
            z, "REPORTINGOWNER.tsv", ["ACCESSION_NUMBER", "RPTOWNERCIK", "RPTOWNER_RELATIONSHIP"]
        )
        tr = table(
            z,
            "NONDERIV_TRANS.tsv",
            [
                "ACCESSION_NUMBER",
                "TRANS_CODE",
                "TRANS_SHARES",
                "TRANS_PRICEPERSHARE",
                "TRANS_ACQUIRED_DISP_CD",
            ],
        )
        tr = tr[
            (tr.TRANS_CODE == code) & (tr.TRANS_ACQUIRED_DISP_CD == ("A" if code == "P" else "D"))
        ]
        tr = tr.assign(
            value=pd.to_numeric(tr.TRANS_SHARES, errors="coerce")
            * pd.to_numeric(tr.TRANS_PRICEPERSHARE, errors="coerce")
        )
        val = tr.groupby("ACCESSION_NUMBER").value.sum()
        insiders = own[
            own.RPTOWNER_RELATIONSHIP.str.contains("Director|Officer", case=False, na=False)
        ]
        n_own = insiders.groupby("ACCESSION_NUMBER").RPTOWNERCIK.nunique()
        s = sub[sub.DOCUMENT_TYPE == "4"].set_index("ACCESSION_NUMBER")
        s = s.join(val, how="inner").join(n_own.rename("owners"), how="inner")
        rows.append(s)
    f = pd.concat(rows)
    f["day"] = pd.to_datetime(f.FILING_DATE, format="mixed", dayfirst=False).dt.normalize()
    f["symbol"] = (
        f.ISSUERTRADINGSYMBOL.str.upper().str.strip().str.replace("-", ".").str.replace("/", ".")
    )
    e = (
        f.groupby(["symbol", "day"])
        .agg(value=("value", "sum"), owners=("owners", "sum"))
        .reset_index()
    )
    return e[e.value >= min_value]


def closes(symbols):
    out = {}
    for s in symbols:
        p = D1 / f"{s}.csv"
        if p.exists() and p.stat().st_size > 60:
            d = pd.read_csv(p, usecols=["ts", "close"])
            day = (
                pd.to_datetime(d.ts, utc=True)
                .dt.tz_convert("America/New_York")
                .dt.tz_localize(None)
                .dt.normalize()
            )
            out[s] = pd.Series(d.close.to_numpy(float), index=day).groupby(level=0).last()
    return pd.DataFrame(out)


def event_returns(e, sign=1.0):
    """Abnormal 20-day return (bp) per event in the universe; overlapping events per name skipped."""
    u = pd.read_csv(UNIVERSE)
    members = u.groupby("month").symbol.apply(set).to_dict()
    e = e[
        [s in members.get(d.strftime("%Y-%m"), set()) for s, d in zip(e.symbol, e.day, strict=True)]
    ]
    c = closes(sorted(set(e.symbol)) + ["SPY"])
    days = c["SPY"].dropna().index
    c = c.reindex(days)
    rows, busy = [], {}
    for _, x in e.sort_values(["day", "symbol"]).iterrows():
        i = days.searchsorted(x.day, side="right")  # first trading day after the filing date
        if i + HOLD >= len(days) or days[i + HOLD] > END or days[i] < START:
            continue
        if busy.get(x.symbol, -1) >= i:
            continue
        p0 = c[x.symbol].iloc[i]
        if not np.isfinite(p0):
            continue
        p1 = (
            c[x.symbol].iloc[i : i + HOLD + 1].ffill().iloc[-1]
        )  # delisted inside the hold: last close
        spy = c["SPY"].iloc[i + HOLD] / c["SPY"].iloc[i] - 1
        busy[x.symbol] = i + HOLD
        rows.append((days[i], x.symbol, x.value, x.owners, sign * ((p1 / p0 - 1) - spy) * 1e4))
    return pd.DataFrame(rows, columns=["entry", "symbol", "value", "owners", "ret"])


def nw_se(x, lags=4):
    """Newey-West standard error of the mean (Bartlett weights)."""
    d = np.asarray(x, float) - np.mean(x)
    n = len(d)
    v = (d @ d) / n
    for k in range(1, lags + 1):
        v += 2 * (1 - k / (lags + 1)) * (d[k:] @ d[:-k]) / n
    return (v / n) ** 0.5


def weekly(r, col="ret"):
    return r.groupby(r.entry.dt.to_period("W"))[col].mean()


def power(r):
    w = weekly(r).to_numpy()
    se = nw_se(w)  # dispersion only
    print(
        f"events {len(r)} ({r.entry.min().date()} .. {r.entry.max().date()}), weeks {len(w)}, names {r.symbol.nunique()}; "
        f"event sd {r.ret.std():.0f} bp; weekly-mean NW se {se:.1f} bp: t 3 needs {3 * se:.1f} bp net "
        f"({3 * se + COST:.1f} gross per event, 20 days)"
    )


def run(r, mirror):
    r = r.assign(net=r.ret - COST)
    w = weekly(r, "net")
    t = w.mean() / nw_se(w.to_numpy())
    h1, h2 = r[r.entry.dt.year <= 2018].net.mean(), r[r.entry.dt.year >= 2019].net.mean()
    n2 = (r.ret - 2 * COST).mean()
    nb = w.drop(w.nlargest(2).index).mean()
    kills = {
        "net <= 0": w.mean() <= 0,
        "t < 3.0": t < 3.0,
        "halves": not (h1 > 0 and h2 > 0),
        "doubled cost <= 0": n2 <= 0,
        "without 2 best weeks <= 0": nb <= 0,
    }
    hit = [k for k, v in kills.items() if v]
    print(
        f"events {len(r)}: gross {r.ret.mean():+.1f} bp, net per event {r.net.mean():+.1f}, weekly mean {w.mean():+.1f}, "
        f"NW t {t:.2f}; halves {h1:+.1f} / {h2:+.1f}; doubled cost {n2:+.1f}; without 2 best weeks {nb:+.1f}"
    )
    print("kills hit:", hit or "none", "->", "KILLED" if hit else "PASSED (development)")
    big = (r.owners >= 2) | (r.value >= 1e6)
    print(
        f"reported: dose (>= 2 insiders or >= USD 1 M) {r[big].net.mean():+.1f} (n {big.sum()}) vs rest "
        f"{r[~big].net.mean():+.1f}; by year {r.groupby(r.entry.dt.year).net.mean().round(1).to_dict()}"
    )
    print(
        f"reported: mirror (sales >= USD 1 M, short direction) {len(mirror)} events, gross {mirror.ret.mean():+.1f}, "
        f"net {mirror.ret.mean() - COST:+.1f}"
    )


if __name__ == "__main__":
    step = sys.argv[1]
    if step == "download":
        download()
    else:
        r = event_returns(filings("P", MIN_VALUE))
        if step == "power":
            power(r)
        else:
            run(r, event_returns(filings("S", 1e6), sign=-1.0))
