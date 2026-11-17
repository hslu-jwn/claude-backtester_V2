"""I-104 Wikipedia page-view attention sort (Fable card 9; rule fixed in knowledge/ideas.md, 0b13df4).

Development only (weeks 2016-04 .. 2021-09-13). Mapping ticker -> English article from Wikidata (data/cache/wiki,
queried 2026-11-17 with the user's contact string; US listings only); page views from the Wikimedia REST API (daily,
user agent, all-access). Trade, cost and kills as I-101 (imports its helpers).
Steps: views (download), power (signal-free), run.
Run: .venv/Scripts/python.exe research/screens/2026-11-17_i104_attention_screen.py views | power | run
"""

import importlib.util
import itertools
import json
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path

import numpy as np
import pandas as pd

spec = importlib.util.spec_from_file_location(
    "i101", "research/screens/2026-11-17_i101_short_volume_screen.py"
)
i101 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(i101)

WIKI = Path("data/cache/wiki")
VIEWS = WIKI / "views"
UNIVERSE = Path("data/cache/alpaca_meta/universe.csv")
D1 = Path("data/cache/alpaca_1d")
US = {"New York Stock Exchange", "Nasdaq", "NYSE American", "NASDAQ/Ngs (Global Select Market)"}
START, END = pd.Timestamp("2016-04-01"), pd.Timestamp("2021-09-13")
COST, MIN_BASE = 13.0, 100.0


def mapping():
    """ticker -> list of (article, start, end) from US listings."""
    rows = [
        {k: v["value"] for k, v in x.items()}
        for x in json.loads((WIKI / "wikidata_tickers_wide.json").read_text())
    ]
    w = pd.DataFrame(rows)
    w = w[w.exchLabel.isin(US)].copy()
    w["ticker"] = w.ticker.str.upper().str.replace("-", ".").str.replace("/", ".").str.strip()
    w["article"] = w.article.str.rsplit("/wiki/", n=1).str[-1]
    for c in ("start", "end"):
        w[c] = pd.to_datetime(w.get(c), errors="coerce", utc=True).dt.tz_localize(None)
    return {
        t: g[["item", "article", "start", "end"]].drop_duplicates("item").to_dict("records")
        for t, g in w.groupby("ticker")
    }


def article_for(cands, day):
    """The one item whose listing period covers the day; a ticker with several undated items is dropped (A1)."""
    if len(cands) == 1:
        return cands[0]["article"]
    cover = [
        c
        for c in cands
        if (pd.isna(c["start"]) or c["start"] <= day) and (pd.isna(c["end"]) or day <= c["end"])
    ]
    dated = [c for c in cover if not (pd.isna(c["start"]) and pd.isna(c["end"]))]
    return dated[0]["article"] if len(dated) == 1 else None


def views():
    import keyring

    ua = f"backtester-research/1.0 ({keyring.get_password('backtester-contact', 'email')})"
    m = mapping()
    u = pd.read_csv(UNIVERSE)
    syms = set(u[(u.month >= "2016-04") & (u.month <= "2021-09")].symbol)
    arts = sorted({c["article"] for s in syms if s in m for c in m[s]})
    VIEWS.mkdir(parents=True, exist_ok=True)
    for i, a in enumerate(arts):
        path = VIEWS / f"{urllib.parse.quote(a, safe='')}.csv"
        if path.exists():
            continue
        url = (
            "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/"
            f"{urllib.parse.quote(urllib.parse.unquote(a), safe='')}/daily/20150701/20210914"
        )
        r = subprocess.run(
            ["curl", "-s", "-A", ua, "-w", "\n%{http_code}", url],
            check=False,
            capture_output=True,
            timeout=120,
        )
        body, _, code = r.stdout.rpartition(b"\n")
        items = json.loads(body).get("items", []) if code == b"200" else []
        pd.DataFrame(
            [(x["timestamp"][:8], x["views"]) for x in items], columns=["day", "views"]
        ).to_csv(path, index=False)
        time.sleep(0.2)
        if i % 200 == 0:
            print(f"views {i} / {len(arts)} ({code.decode()})", flush=True)
    print(f"articles {len(arts)}")


def weeks():
    m = mapping()
    u = pd.read_csv(UNIVERSE)
    spy = pd.read_csv(D1 / "SPY.csv", usecols=["ts"]).ts
    days = pd.DatetimeIndex(
        pd.to_datetime(spy, utc=True)
        .dt.tz_convert("America/New_York")
        .dt.tz_localize(None)
        .dt.normalize()
        .unique()
    ).sort_values()
    entries = pd.Series(days, index=days).groupby(days.to_period("W-SUN")).min()
    entries = [d for d in entries if START <= d]
    c = i101.closes(sorted(u.symbol.unique()))
    cache = {}

    def series(a):
        if a not in cache:
            p = VIEWS / f"{urllib.parse.quote(a, safe='')}.csv"
            v = (
                pd.read_csv(p)
                if p.exists() and p.stat().st_size > 20
                else pd.DataFrame(columns=["day", "views"])
            )
            cache[a] = pd.Series(v.views.to_numpy(float), index=pd.to_datetime(v.day.astype(str)))
        return cache[a]

    out, mapped_share = [], []
    for e, x in itertools.pairwise(entries):
        if x > END:
            break
        members = u[u.month == e.strftime("%Y-%m")].symbol
        rows = []
        for s in members:
            a = article_for(m[s], e) if s in m else None
            if a is None or s not in c.columns:
                continue
            v = series(a)
            last = v[(v.index >= e - pd.Timedelta(days=7)) & (v.index < e)].sum()
            base = (
                v[
                    (v.index >= e - pd.Timedelta(days=63)) & (v.index < e - pd.Timedelta(days=7))
                ].sum()
                / 8
            )
            if base < MIN_BASE:
                continue
            p0, p1 = c.loc[:e, s].iloc[-1], c.loc[:x, s].ffill().iloc[-1]
            if e in c.index and np.isfinite(c.loc[e, s]):
                rows.append((s, last / base, (p1 / p0 - 1) * 1e4))
        mapped_share.append(len(rows) / max(len(members), 1))
        f = pd.DataFrame(rows, columns=["sym", "sig", "ret"]).set_index("sym")
        if len(f) >= 100:
            out.append((e, f))
    print(
        f"weeks {len(out)}, names with a signal per week median {int(np.median([len(f) for _, f in out]))} "
        f"(share of the universe {np.median(mapped_share):.2f})"
    )
    return out


if __name__ == "__main__":
    step = sys.argv[1]
    if step == "views":
        views()
    else:
        ws = weeks()
        i101.COST = COST
        i101.power(ws) if step == "power" else i101.run(ws)
