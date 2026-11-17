"""I-112 month-end duration extension in euro, UK and Japanese government bonds (rule in knowledge/ideas.md, e79b3ca).

Data (public, curl's own user agent): ECB AAA 10-year spot, Bank of England nominal spot 10-year (xlsx, read with the
standard library), MOF JGB 10-year -> data/cache/intl_yields/{EU,UK,JP}.csv (day, yield in %).
Steps: download, power (signal-free), run (development), test (rule fixed in the card).
Run: .venv/Scripts/python.exe research/screens/2026-11-17_i112_intl_month_end_screen.py download | power | run | test
"""

import importlib.util
import io
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

spec = importlib.util.spec_from_file_location(
    "i109", Path(__file__).parent / "2026-11-17_i109_treasury_month_end_screen.py"
)
i109 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(i109)

ROOT = Path("data/cache/intl_yields")
ECB = "https://data-api.ecb.europa.eu/service/data/YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_10Y?format=csvdata"
MOF = "https://www.mof.go.jp/english/policy/jgbs/reference/interest_rate/historical/jgbcme_all.csv"
BOE = "https://www.bankofengland.co.uk/-/media/boe/files/statistics/yield-curves/glcnominalddata.zip"
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
RNS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
COST = 2.0
MARKETS = ("EU", "UK", "JP")


def get(url):
    return subprocess.run(["curl", "-s", "-f", "-L", url], check=True, capture_output=True, timeout=600).stdout


def col(ref):
    letters = re.match(r"[A-Z]+", ref)[0]
    n = 0
    for ch in letters:
        n = n * 26 + ord(ch) - 64
    return n - 1


def xlsx_sheet(raw, name_part):
    """Rows (list of {col index: value}) of the first sheet whose name contains `name_part`."""
    z = zipfile.ZipFile(io.BytesIO(raw))
    shared = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS):
            shared.append("".join(t.text or "" for t in si.iter(f"{{{NS['m']}}}t")))
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rid = next(s.get(RNS) for s in wb.iter(f"{{{NS['m']}}}sheet") if name_part in s.get("name").lower())
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    target = next(r.get("Target") for r in rels if r.get("Id") == rid).lstrip("/")
    target = target if target.startswith("xl/") else "xl/" + target
    rows = []
    for row in ET.fromstring(z.read(target)).iter(f"{{{NS['m']}}}row"):
        cells = {}
        for c in row.findall("m:c", NS):
            v = c.find("m:v", NS)
            if v is None:
                continue
            cells[col(c.get("r"))] = shared[int(v.text)] if c.get("t") == "s" else v.text
        rows.append(cells)
    return rows


def boe(raw_zip):
    out = {}
    outer = zipfile.ZipFile(io.BytesIO(raw_zip))
    for name in sorted(outer.namelist()):
        rows = xlsx_sheet(outer.read(name), "spot curve")
        head = next(r for r in rows[:10] if any(_num(v) == 10.0 for k, v in r.items() if k > 0))
        c10 = next(k for k, v in head.items() if k > 0 and _num(v) == 10.0)
        for r in rows:
            d, y = _num(r.get(0)), _num(r.get(c10))
            if d and y is not None and 20000 < d < 80000:
                out[pd.Timestamp("1899-12-30") + pd.Timedelta(days=int(d))] = y
    return pd.Series(out).sort_index()


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def download():
    ROOT.mkdir(parents=True, exist_ok=True)
    e = pd.read_csv(io.BytesIO(get(ECB)), usecols=["TIME_PERIOD", "OBS_VALUE"])
    s = {"EU": pd.Series(e.OBS_VALUE.to_numpy(float), index=pd.to_datetime(e.TIME_PERIOD))}
    j = pd.read_csv(io.BytesIO(get(MOF)), skiprows=1, na_values="-")
    s["JP"] = pd.Series(j["10Y"].to_numpy(float), index=pd.to_datetime(j.Date, format="%Y/%m/%d"))
    s["UK"] = boe(get(BOE))
    for k, v in s.items():
        v = v.dropna().sort_index()
        v = v[~v.index.duplicated()]
        v.rename_axis("day").rename("y").to_csv(ROOT / f"{k}.csv")
        print(k, v.index[0].date(), v.index[-1].date(), len(v))


def returns(market, start, end):
    y = pd.read_csv(ROOT / f"{market}.csv", parse_dates=["day"], index_col="day").y.loc[start:end] / 100
    safe = y.where(y.abs() > 1e-6, 1e-6)  # JGB 10-year at exactly 0 %: the formula's limit (duration -> 10)
    dur = (1 - (1 + safe / 2) ** (-20)) / safe  # I-109's 10-year par-bond duration (A2)
    return (-dur.shift(1) * y.diff() * 1e4).dropna()


def table(start, end, offset=0):
    """Month x market net excess (bp) and the pooled mean."""
    t = pd.DataFrame({m: i109.months(returns(m, start, end), offset).excess - COST for m in MARKETS})
    t["pooled"] = t[list(MARKETS)].mean(axis=1)
    return t


def power():
    s, e = "1990-01-01", "2021-08-31"
    sd = np.mean([table(s, e, k).pooled.std() for k in (5, 8, 11, 14)])
    n = len(table(s, e).pooled.dropna())
    se = sd / np.sqrt(n)
    print(f"pooled months {n}; signal-free sd {sd:.1f} bp, se {se:.1f}: t 3 needs {3 * se:.1f} bp net")
    for m in MARKETS:
        r = returns(m, s, e)
        print(f"  {m}: {r.index[0].date()} .. {r.index[-1].date()}, {r.index.to_period('M').nunique()} months")


def run():
    t = table("1990-01-01", "2021-08-31")
    p = t.pooled.dropna()
    tt = i109.tstat(p)
    h1, h2 = p[p.index.year <= 2005].mean(), p[p.index.year >= 2006].mean()
    n2 = (p - COST).mean()
    nb = p.drop(p.nlargest(2).index).mean()
    each = {m: t[m].dropna().mean() for m in MARKETS}
    kills = {
        "net <= 0": p.mean() <= 0,
        "t < 3.0": tt < 3.0,
        "halves": not (h1 > 0 and h2 > 0),
        "doubled cost <= 0": n2 <= 0,
        "without 2 best <= 0": nb <= 0,
        "breadth": min(each.values()) <= 0,
    }
    hit = [k for k, v in kills.items() if v]
    print(
        f"pooled months {len(p)}: net {p.mean():+.1f} bp, t {tt:.2f}; halves {h1:+.1f} / {h2:+.1f}; doubled {n2:+.1f}; "
        f"without 2 best {nb:+.1f} -> {'KILLED ' + str(hit) if hit else 'PASSED (development)'}"
    )
    us = i109.months(i109.returns("DGS10")).excess
    for m in MARKETS:
        x = t[m].dropna()
        print(f"  {m}: {len(x)} months, net {x.mean():+.1f}, t {i109.tstat(x):.2f}; corr with US excess "
              f"{x.corr(us.reindex(x.index)):.2f}")


def test():
    t = table("2021-09-01", "2100-01-01")
    last = min(pd.read_csv(ROOT / f"{m}.csv", parse_dates=["day"]).day.max().to_period("M") for m in MARKETS)
    t = t.loc["2021-10" : str(last - 1)]  # whole months only: the month before the last data month
    p = t.pooled
    each = {m: t[m].mean() for m in MARKETS}
    g = {"pooled net > 0": p.mean() > 0, "t >= 1.5": i109.tstat(p) >= 1.5, "doubled > 0": (p - COST).mean() > 0,
         "2 of 3 markets > 0": sum(v > 0 for v in each.values()) >= 2}
    verdict = "PASSED" if all(g.values()) else ("FALSIFIED" if p.mean() <= 0 else "NOT CONFIRMED")
    print(f"test months {len(p)} ({p.index[0]} .. {p.index[-1]}): pooled net {p.mean():+.1f}, t {i109.tstat(p):.2f}; "
          f"markets { {k: round(v, 1) for k, v in each.items()} }")
    print("gates:", g, "->", verdict)


if __name__ == "__main__":
    {"download": download, "power": power, "run": run, "test": test}[sys.argv[1]]()
