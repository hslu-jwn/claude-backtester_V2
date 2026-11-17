"""I-107 fails-to-deliver intensity, half-monthly sort (rule fixed in knowledge/ideas.md, c449026).

SEC cnsfails files 2016-01 .. 2021-08 (data/cache/sec_ftd, user's contact string), Alpaca daily bars, universe
docs/share-universe.md. Development only. Steps: download, power (signal-free), run.
Run: .venv/Scripts/python.exe research/screens/2026-11-17_i107_fails_screen.py download | power | run
"""

import io
import itertools
import re
import subprocess
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

FTD = Path("data/cache/sec_ftd")
D1 = Path("data/cache/alpaca_1d")
UNIVERSE = Path("data/cache/alpaca_meta/universe.csv")
PAGE = "https://www.sec.gov/data-research/sec-markets-data/fails-deliver-data"
HALVES = [
    f"{y}{m:02d}{h}"
    for y in range(2016, 2022)
    for m in range(1, 13)
    for h in "ab"
    if (y, m) <= (2021, 8)
]
END = pd.Timestamp("2021-09-13")
COST = 13.0


def download():
    import keyring

    ua = f"backtester-research {keyring.get_password('backtester-contact', 'email')}"
    FTD.mkdir(parents=True, exist_ok=True)
    page = subprocess.run(
        ["curl", "-s", "-L", "-A", ua, PAGE], check=True, capture_output=True, timeout=120
    ).stdout
    links = {  # some files carry a suffix (cnsfails201910a_0.zip)
        f"cnsfails{h}.zip": m
        for m, h in re.findall(r'href="(/files/[^"]*cnsfails(\d{6}[ab])(?:_\d+)?\.zip)"', page.decode())
    }
    for h in HALVES:
        path = FTD / f"cnsfails{h}.zip"
        if path.exists():
            continue
        r = subprocess.run(
            [
                "curl",
                "-s",
                "-A",
                ua,
                "-w",
                "\n%{http_code}",
                "https://www.sec.gov" + links[f"cnsfails{h}.zip"],
            ],
            check=False,
            capture_output=True,
            timeout=300,
        )
        body, _, code = r.stdout.rpartition(b"\n")
        if code != b"200":
            raise RuntimeError(f"SEC HTTP {code.decode()} for {h}")
        path.write_bytes(body)
    print(f"{len(HALVES)} files")


def fails():
    rows = []
    for h in HALVES:
        z = zipfile.ZipFile(io.BytesIO((FTD / f"cnsfails{h}.zip").read_bytes()))
        raw = z.read(z.namelist()[0]).decode("latin-1")
        d = pd.read_csv(io.StringIO(raw), sep="|", dtype=str, on_bad_lines="skip")
        d.columns = [c.strip().upper() for c in d.columns]
        d = d[pd.to_numeric(d["SETTLEMENT DATE"], errors="coerce").notna()]
        val = pd.to_numeric(d["QUANTITY (FAILS)"], errors="coerce") * pd.to_numeric(
            d["PRICE"], errors="coerce"
        )
        g = pd.DataFrame({"symbol": d.SYMBOL.str.strip().str.upper(), "value": val}).dropna()
        rows.append(g.groupby("symbol").value.sum().rename(h))
    return pd.concat(rows, axis=1).fillna(0.0)  # symbol x half-month: fails value (USD)


def daily(symbols):
    c, dv = {}, {}
    for s in symbols:
        p = D1 / f"{s}.csv"
        if p.exists() and p.stat().st_size > 60:
            d = pd.read_csv(p, usecols=["ts", "close", "volume"])
            day = (
                pd.to_datetime(d.ts, utc=True)
                .dt.tz_convert("America/New_York")
                .dt.tz_localize(None)
                .dt.normalize()
            )
            d.index = day
            d = d[~d.index.duplicated()]
            c[s], dv[s] = d.close, d.close * d.volume
    return pd.DataFrame(c), pd.DataFrame(dv)


def periods():
    """List of (availability day, next availability day, frame of symbol -> intensity, ret bp)."""
    f = fails()
    u = pd.read_csv(UNIVERSE)
    members = u.groupby("month").symbol.apply(list).to_dict()
    c, dv = daily(sorted(u.symbol.unique()) + ["SPY"])
    days = c["SPY"].dropna().index
    c, dv = c.reindex(days), dv.reindex(days)

    def span(h):
        y, m = int(h[:4]), int(h[4:6])
        first = pd.Timestamp(y, m, 1) if h[-1] == "a" else pd.Timestamp(y, m, 16)
        last = (
            pd.Timestamp(y, m, 15)
            if h[-1] == "a"
            else (pd.Timestamp(y, m, 1) + pd.offsets.MonthEnd(0))
        )
        nxt = pd.Timestamp(y, m, 1) + pd.offsets.MonthBegin(1)
        avail = nxt if h[-1] == "a" else nxt + pd.Timedelta(days=15)
        return (
            first,
            last,
            days[days.searchsorted(avail)] if days.searchsorted(avail) < len(days) else None,
        )

    sched = [(h, *span(h)) for h in HALVES]
    out = []
    for (h, first, last, av), (_, _, _, nxt) in itertools.pairwise(sched):
        if av is None or nxt is None or nxt > END or av < pd.Timestamp("2016-04-01"):
            continue
        m = [s for s in members.get(av.strftime("%Y-%m"), []) if s in c.columns]
        sdv = dv.loc[first:last, m].sum()
        inten = (f[h].reindex(m).fillna(0.0) / sdv.where(sdv > 0)).dropna()
        p0, p1 = c.loc[av, inten.index], c.loc[:nxt, inten.index].ffill().iloc[-1]
        ret = ((p1 / p0 - 1) * 1e4).where(p0.notna())
        fr = pd.DataFrame({"x": inten, "ret": ret}).dropna()
        out.append((av, nxt, fr))
    return out


def split(fr, rng=None):
    pos = fr[fr.x > 0]
    hi = pos.sort_values(["x"], kind="mergesort").iloc[-max(len(pos) // 10, 1) :]
    lo = fr[fr.x == 0]
    if rng is not None:  # signal-free: random high group of the same size, the rest as low
        idx = rng.permutation(fr.index)
        hi, lo = fr.loc[idx[: len(hi)]], fr.loc[idx[len(hi) :]]
    return (
        lo.ret.mean() - hi.ret.mean(),
        len(hi),
        len(lo),
    )  # cell A: long no-fails, short high-fails


def tstat(x):
    x = np.asarray(x, float)
    return x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))


def power(ps):
    rng = np.random.default_rng(1)
    sd = np.mean([np.std([split(fr, rng)[0] for _, _, fr in ps], ddof=1) for _ in range(100)])
    se = sd / np.sqrt(len(ps))
    sizes = [split(fr)[1:] for _, _, fr in ps]
    print(
        f"periods {len(ps)} ({ps[0][0].date()} .. {ps[-1][1].date()}), high group median {int(np.median([a for a, _ in sizes]))}, "
        f"zero-fails group median {int(np.median([b for _, b in sizes]))}; POWER: random-split sd {sd:.0f} bp, se {se:.1f}: "
        f"|t| 3.3 needs {3.3 * se:.0f} bp net per half-month (+ {COST:.0f})"
    )


def run(ps):
    idx = [a for a, _, _ in ps]
    g = pd.Series([split(fr)[0] for _, _, fr in ps], index=idx)
    print(
        f"periods {len(g)}: gross cell A (long no-fails, short high) {g.mean():+.1f} bp, gross t {tstat(g):.2f}"
    )
    for cell, d in (("A long no-fails / short high", 1), ("B long high / short no-fails", -1)):
        net = d * g - COST
        t = tstat(net)
        h1, h2 = net[net.index.year <= 2018].mean(), net[net.index.year >= 2019].mean()
        n2 = (d * g - 2 * COST).mean()
        nb = net.drop(net.nlargest(2).index).mean()
        kills = {
            "|t| < 3.3": t < 3.3,
            "net <= 0": net.mean() <= 0,
            "halves": not (h1 > 0 and h2 > 0),
            "doubled cost <= 0": n2 <= 0,
            "without 2 best <= 0": nb <= 0,
        }
        hit = [k for k, v in kills.items() if v]
        print(
            f"cell {cell}: net {net.mean():+.1f}, t {t:.2f}; halves {h1:+.1f} / {h2:+.1f}; doubled {n2:+.1f}; "
            f"without 2 best {nb:+.1f} -> {'KILLED ' + str(hit) if hit else 'PASSED (development)'}"
        )
        print(f"  years {net.groupby(net.index.year).mean().round(1).to_dict()}")


if __name__ == "__main__":
    step = sys.argv[1]
    if step == "download":
        download()
    else:
        ps = periods()
        power(ps) if step == "power" else run(ps)
