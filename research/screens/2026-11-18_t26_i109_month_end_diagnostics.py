"""T-26 I-109 month-end diagnostics (card knowledge/ideas.md T-26). Sensitivity on spent data; the registered
result stands. Splits I-109's registered net (DGS10, last 3 trade dates, excess - 2 bp) of development
(1990-01 .. 2021-08) and test (2021-10 .. 2026-10) by:
  (a) quarter-end months (Mar / Jun / Sep / Dec: repo stress, and the ZN expiry months) vs the other months;
  (b) months where a 2- / 5- / 7-year note settled on one of the window's trade dates vs not (TreasuryDirect).
Flags fixed before the run: CONCENTRATED if one side's mean net <= 25 % of the full mean (or <= 0) while the other
side carries it; reported with each side's t and the difference t (Welch). Expiry is not split apart from (a): the
ZN expiry months are the quarter-end months, and the DGS10 statistic has no contract.
Run: .venv/Scripts/python.exe research/screens/2026-11-18_t26_i109_month_end_diagnostics.py download | run
"""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

spec = importlib.util.spec_from_file_location(
    "i109", Path(__file__).with_name("2026-11-17_i109_treasury_month_end_screen.py")
)
i109 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(i109)

NOTES = Path("data/cache/treasurydirect/notes.json")
URL = "https://www.treasurydirect.gov/TA_WS/securities/search?format=json&type=Note&dateFieldName=issueDate"


def download():
    NOTES.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for y in range(1990, 2027):
        body = subprocess.run(
            ["curl", "-s", "-f", "-m", "120", f"{URL}&startDate=01/01/{y}&endDate=12/31/{y}"],
            check=True,
            capture_output=True,
        ).stdout
        rows += [{k: r[k] for k in ("securityTerm", "issueDate")} for r in json.loads(body)]
        print(y, len(rows))
    NOTES.write_text(json.dumps(rows))


def settle_days():
    """Issue (settlement) dates of 2-, 5- and 7-year notes, original issues and reopenings."""
    d = pd.DataFrame(json.loads(NOTES.read_text()))
    d = d[d.securityTerm.str.match(r"^(2|5|7)-Year")]
    return set(pd.to_datetime(d.issueDate).dt.normalize())


def windows(r):
    """Per month: the trade dates of I-109's window (the last 3)."""
    return {m: set(g.index[-3:]) for m, g in r.groupby(r.index.to_period("M")) if len(g) > 3}


def tstat(x):
    return i109.tstat(x) if len(x) > 1 else float("nan")


def split(name, net, mask):
    a, b = net[mask], net[~mask]
    full = net.mean()
    welch = (a.mean() - b.mean()) / np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    weak = [s for s, x in (("in", a), ("out", b)) if x.mean() <= 0.25 * full]
    flag = f"CONCENTRATED ({weak[0]} side weak)" if len(weak) == 1 else "spread"
    print(
        f"  {name}: in {a.mean():+.1f} bp (n {len(a)}, t {tstat(a):.2f}) | out {b.mean():+.1f} (n {len(b)}, "
        f"t {tstat(b):.2f}) | diff t {welch:.2f} -> {flag}"
    )


def run():
    settles = settle_days()
    for label, start, end, months in (
        ("development", i109.START, i109.END, slice("1990-01", "2021-08")),
        ("test", "2021-09-14", "2026-10-31", slice("2021-10", "2026-10")),
    ):
        r = i109.returns("DGS10", start, end)
        e = i109.months(r).loc[months]
        net = e.excess - i109.COST
        w = windows(r)
        quarter = pd.Series(net.index.month % 3 == 0, index=net.index)
        settle = pd.Series([bool(w[m] & settles) for m in net.index], index=net.index)
        print(f"{label}: {len(net)} months, net {net.mean():+.1f} bp (t {tstat(net):.2f})")
        split("(a) quarter-end months", net, quarter)
        split("(b) 2/5/7-year settlement in window", net, settle)


if __name__ == "__main__":
    {"download": download, "run": run}[sys.argv[1]]()
