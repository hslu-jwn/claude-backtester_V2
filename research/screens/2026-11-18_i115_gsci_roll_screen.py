"""I-115 S&P GSCI roll front-running in energy calendar spreads (rule in knowledge/ideas.md, 522df40; Mou 2010).

Data (public, curl): EIA daily futures settlements, contracts 1-3, CL / HO / RB / NG -> data/cache/eia_strips/
(development rows only, to DEV_END). Steps: download, power (signal-free sd), run (development), test_download, test (rule in the card, auto decision 50).
Run: .venv/Scripts/python.exe research/screens/2026-11-18_i115_gsci_roll_screen.py download | power | run | test_download | test
"""

import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("data/cache/eia_strips")
TEST_ROOT = Path("data/cache/eia_strips_test")
DEV_END = pd.Timestamp("2021-09-13")
PET = "https://www.eia.gov/dnav/pet/hist/LeafHandler.ashx?n=PET&s={s}&f=D"
NG = "https://www.eia.gov/dnav/ng/hist/rngc{k}d.htm"
SERIES = {
    "CL": [PET.format(s=f"RCLC{k}") for k in (1, 2, 3)],
    "HO": [PET.format(s=f"EER_EPD2F_PE{k}_Y35NY_DPG") for k in (1, 2, 3)],
    "RB": [PET.format(s=f"EER_EPMRR_PE{k}_Y35NY_DPG") for k in (1, 2, 3)],
    "NG": [NG.format(k=k) for k in (1, 2, 3)],
}
MONTHS = {
    m: i
    for i, m in enumerate(
        ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1
    )
}
COST = 3.0  # bp of collateral per tranche round trip
FIRST, LAST = (2000, 1), (2021, 8)
PLACEBO = ((1986, 1), (1999, 12))


def parse(html):
    """EIA weekly-row table: label 'YYYY Mon-DD to ...' then Mon..Fri cells."""
    out = {}
    for row in re.findall(r"<tr>(.*?)</tr>", html, re.DOTALL):
        lab = re.search(r"class='B6'>(?:&nbsp;)*(\d{4}) (\w{3})-\s?(\d+)", row)
        if not lab:
            continue
        start = pd.Timestamp(int(lab[1]), MONTHS[lab[2]], int(lab[3]))
        cells = re.findall(r"<td class='B3'>([^<]*)</td>", row)
        for i, v in enumerate(cells[:5]):
            if v.strip():
                out[start + pd.Timedelta(days=i)] = float(v.replace(",", ""))
    return pd.Series(out).sort_index()


def download(root=ROOT, end=DEV_END):
    root.mkdir(parents=True, exist_ok=True)
    for com, urls in SERIES.items():
        cols = {}
        for k, url in enumerate(urls, 1):
            html = subprocess.run(
                ["curl", "-s", "-f", "-L", url], capture_output=True, check=True, timeout=300
            ).stdout
            cols[f"c{k}"] = parse(html.decode("latin1"))
        df = pd.DataFrame(cols)
        df.index.name = "day"
        df[df.index <= end].to_csv(root / f"{com}.csv")
        print(com, df.index.min().date(), min(df.index.max(), end).date(), len(df[df.index <= end]))


def load(root=ROOT):
    return {
        com: pd.read_csv(root / f"{com}.csv", parse_dates=["day"], index_col="day")
        for com in SERIES
    }


def add_months(ym, n):
    y, m = ym
    k = y * 12 + (m - 1) + n
    return (k // 12, k % 12 + 1)


class Book:
    def __init__(self, data):
        self.data = data
        self.bdays = data["CL"]["c1"].dropna().index
        self._exp = {}

    def month_days(self, ym):
        b = self.bdays
        return b[(b.year == ym[0]) & (b.month == ym[1])]

    def expiry(self, com, d):
        """Last trade date of delivery month d (card rules); None if the month has no business days in the data."""
        key = (com, d)
        if key not in self._exp:
            days = self.month_days(add_months(d, -1))
            if len(days) < 3:
                self._exp[key] = None
            elif com == "CL":
                upto = days[days <= pd.Timestamp(days[0].year, days[0].month, 25)]
                i = self.bdays.get_loc(upto[-1])
                self._exp[key] = self.bdays[i - 3]
            elif com in ("HO", "RB"):
                self._exp[key] = days[-1]
            else:
                self._exp[key] = days[-3]
        return self._exp[key]

    def price(self, com, d, day):
        """Settlement of delivery month d on `day` from the EIA position it occupies (1-3)."""
        pos = 1
        for back in range(1, 5):
            e = self.expiry(com, add_months(d, -back))
            if e is None:
                return None
            if e >= day:
                pos += 1
        if pos > 3 or day not in self.data[com].index:
            return None
        v = self.data[com].at[day, f"c{pos}"]
        return None if pd.isna(v) else float(v)

    def month(self, com, ym, entry_off, hold):
        """Mean bp return of 5 tranches: entry at R1 + entry_off + k - 1, exit `hold` business days later."""
        days = self.month_days(ym)
        if len(days) < 9:
            return None
        i1 = self.bdays.get_loc(days[4])
        held, nxt = add_months(ym, 1), add_months(ym, 2)
        rs = []
        for k in range(5):
            a, b = i1 + entry_off + k, i1 + entry_off + k + hold
            if a < 0 or b >= len(self.bdays):
                return None
            d0, d1 = self.bdays[a], self.bdays[b]
            h0, h1, n0, n1 = (
                self.price(com, held, d0),
                self.price(com, held, d1),
                self.price(com, nxt, d0),
                self.price(com, nxt, d1),
            )
            if None in (h0, h1, n0, n1) or h0 + n0 <= 0:
                return None
            rs.append(1e4 * ((h0 - h1) + (n1 - n0)) / ((h0 + n0) / 2))
        return float(np.mean(rs))


def months(first, last):
    ym = first
    while ym <= last:
        yield ym
        ym = add_months(ym, 1)


def table(book, first, last, entry_off=-10, hold=10):
    rows = []
    for ym in months(first, last):
        r = {com: book.month(com, ym, entry_off, hold) for com in SERIES}
        rows.append({"month": pd.Timestamp(ym[0], ym[1], 1), **r})
    df = pd.DataFrame(rows).set_index("month").astype(float)
    df["energy"] = df[list(SERIES)].mean(axis=1)
    return df


def tstat(x):
    x = pd.Series(x).dropna()
    return len(x), x.mean(), x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))


def line(name, x):
    n, m, t = tstat(x)
    return f"{name:<36} n {n:4d}  mean {m:7.1f} bp  t {t:5.2f}"


def power():
    book = Book(load())
    sds = []
    for off in (
        0,
        3,
        6,
        9,
    ):  # the same 10-day spread trade starting at R1 or later (after the build window)
        sds.append(table(book, FIRST, LAST, entry_off=off)["energy"].std(ddof=1))
    sd = float(np.mean(sds))
    n = len(list(months(FIRST, LAST)))
    se = sd / np.sqrt(n)
    print(
        f"signal-free energy-month sd {sd:.1f} bp (offsets 0/3/6/9 after R1: {', '.join(f'{s:.1f}' for s in sds)}); "
        f"{n} months: se {se:.1f}, t 3 needs {3 * se + COST:.1f} bp gross ({3 * se:.1f} net)"
    )


def run():
    book = Book(load())
    s1 = table(book, FIRST, LAST)
    missing = s1[list(SERIES)].isna().sum().to_dict()
    print("commodity-months without 5 tranches (incl. RB before 2005-10):", missing)
    net = s1["energy"] - COST
    _, m, t = tstat(net)
    half = s1.index <= pd.Timestamp("2010-12-01")
    com_net = {com: (s1[com] - COST).mean() for com in SERIES}
    gates = {
        "net > 0": m > 0,
        "t >= 3.0": t >= 3.0,
        "halves both > 0": net[half].mean() > 0 and net[~half].mean() > 0,
        "doubled cost > 0": (s1["energy"] - 2 * COST).mean() > 0,
        "without 2 best > 0": net.drop(net.nlargest(2).index).mean() > 0,
        "CL net > 0": com_net["CL"] > 0,
        ">= 3 of 4 net > 0": sum(v > 0 for v in com_net.values()) >= 3,
    }
    print(line("S1 energy (gated)", net))
    print(line("  gross", s1["energy"]))
    print(line("  halves 2000-2010", net[half]))
    print(line("  halves 2011-2021", net[~half]))
    print(line("  doubled cost", s1["energy"] - 2 * COST))
    print(line("  without 2 best", net.drop(net.nlargest(2).index)))
    for com in SERIES:
        print(line(f"  {com}", s1[com] - COST))
    for name, ok in gates.items():
        print(f"  gate {name:<20} {'pass' if ok else 'FAIL'}")
    print("VERDICT:", "PASSED every development gate" if all(gates.values()) else "KILLED")
    print("reported, not gated:")
    s2 = table(book, FIRST, LAST, entry_off=-5, hold=5)
    print(line("S2 energy (5..1 days before)", s2["energy"] - COST))
    pl = table(book, *PLACEBO)
    print(line("placebo 1986-1999 S1 energy", pl["energy"] - COST))
    for com in SERIES:
        print(line(f"  placebo {com}", pl[com] - COST))
    after = table(book, FIRST, LAST, entry_off=0)
    print(line("window 10 days later (after roll)", after["energy"] - COST))
    print(
        line(
            "2000-2010-03 (Mou's window) S1",
            (s1["energy"] - COST)[s1.index <= pd.Timestamp("2010-03-01")],
        )
    )
    print("by year (S1 energy net bp per month, mean):")
    for year, g in net.groupby(net.index.year):
        print(f"  {year}  {g.mean():7.1f}  n {g.notna().sum():2d}")


def test_download():
    download(TEST_ROOT, pd.Timestamp("2030-01-01"))


def test():
    book = Book(load(TEST_ROOT))
    s1 = table(book, (2021, 10), (2024, 3))
    print("commodity-months without 5 tranches:", s1[list(SERIES)].isna().sum().to_dict())
    net = s1["energy"] - COST
    _, m, t = tstat(net)
    gates = {
        "net > 0": m > 0,
        "t >= 1.5": t >= 1.5,
        "doubled cost > 0": (s1["energy"] - 2 * COST).mean() > 0,
    }
    print(line("I-115 test S1 energy (gated)", net))
    print(line("  gross", s1["energy"]))
    print(line("  doubled cost", s1["energy"] - 2 * COST))
    for com in SERIES:
        print(line(f"  {com}", s1[com] - COST))
    for name, ok in gates.items():
        print(f"  gate {name:<20} {'pass' if ok else 'FAIL'}")
    print(
        "VERDICT:",
        "PASSED" if all(gates.values()) else ("FALSIFIED" if m <= 0 else "NOT CONFIRMED"),
    )
    after = table(book, (2021, 10), (2024, 3), entry_off=0)
    print(line("reported: window 10 days later", after["energy"] - COST))
    for year, g in net.groupby(net.index.year):
        print(f"  {year}  {g.mean():7.1f}  n {g.notna().sum():2d}")


if __name__ == "__main__":
    {
        "download": download,
        "power": power,
        "run": run,
        "test_download": test_download,
        "test": test,
    }[sys.argv[1]]()
