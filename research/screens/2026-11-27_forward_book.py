"""Forward book (FBK; docs/research-runner.md > Forward book, rule set by the user 2026-11-27). Reporting only.

One weekly book over the forward logs in research/forward/: every tradable shelf row plus Strategy 19 / 20 (Monday,
not liquid). Registered inputs only (the MEMBERS table); forward data is never used to size.
- Weekly unit: a member's net per period is summed into ISO weeks (Monday 00:00 UTC, by the period's date) and divided
  by its registered weekly sd = sd_period x sqrt(periods per week). A week without a period counts 0.
- Weight w_i ~ shrunk weekly Sharpe = factor x mean_week / sd_week (M10: 0.65 PASSED, 0.4 UNPROVEN / POOLED-POSITIVE),
  normalised to sum 1; a non-positive shrunk Sharpe gets 0. Correlations are assumed 0 (stated in the output).
Run: .venv/Scripts/python.exe research/screens/2026-11-27_forward_book.py report
"""

import math
import sys
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

FORWARD = Path("research/forward")


def _weeks(a: date, b: date) -> float:
    return (b - a).days / 7


@dataclass(frozen=True)
class Member:
    name: str
    file: str  # under research/forward/
    date_col: str  # "period" (shelf logs) or "entry_time" (Strategy 19 / 20 logs)
    col: str  # net column: net_bp or net_r
    unit: str
    ppw: float  # periods per week at registration
    mean: float  # registered net mean per period (own unit)
    sd: float  # registered sd per period (own unit)
    factor: float  # M10 shrink: 0.65 PASSED, 0.4 UNPROVEN-POSITIVE / POOLED-POSITIVE
    source: str


# sd per period = ledger `se` x sqrt(n) (se = sd / sqrt(n)); means are the registered net means.
# Later POOLED-POSITIVE rows: add one line here.
MEMBERS = (
    # ledger I100: net +107.1 bp/week (153 weeks), se 43.71 -> sd 540.7; M1 UNPROVEN-POSITIVE
    Member(
        "shelf_i100",
        "shelf_i100.csv",
        "period",
        "net_bp",
        "bp",
        1,
        107.1,
        43.71 * math.sqrt(153),
        0.4,
        "ledger I100",
    ),
    # ledger I84: net +70.5 bp/week (186 weeks), se 40.06; M1 UNPROVEN-POSITIVE
    Member(
        "shelf_i84",
        "shelf_i84.csv",
        "period",
        "net_bp",
        "bp",
        1,
        70.5,
        40.06 * math.sqrt(186),
        0.4,
        "ledger I84",
    ),
    # ledger I98: net +12.0 bp/week (186 weeks), se 6.522; M1 UNPROVEN-POSITIVE
    Member(
        "shelf_i98",
        "shelf_i98.csv",
        "period",
        "net_bp",
        "bp",
        1,
        12.0,
        6.522 * math.sqrt(186),
        0.4,
        "ledger I98",
    ),
    # ledger H11: net +0.040 R/trade dev (413 trades 2015-01-02..2021-09-13), se 0.0138 (gross est row); UNPROVEN-POSITIVE
    Member(
        "shelf_h11",
        "shelf_h11.csv",
        "period",
        "net_r",
        "R",
        413 / _weeks(date(2015, 1, 2), date(2021, 9, 13)),
        0.040,
        0.0138 * math.sqrt(413),
        0.4,
        "ledger H11",
    ),
    # ledger I71: net +9.0 bp/event (83 events 2010-01-01..2021-09-13, card text), se 4.167 (gross est row); UNPROVEN-POSITIVE
    Member(
        "shelf_i71",
        "shelf_i71.csv",
        "period",
        "net_bp",
        "bp",
        83 / _weeks(date(2010, 1, 1), date(2021, 9, 13)),
        9.0,
        4.167 * math.sqrt(83),
        0.4,
        "ledger I71",
    ),
    # I-143 left out (Opus 2026-11-27): registered forward only, no verdict, and its numbers are I-105's (not executable);
    # it joins only on POOLED-POSITIVE or better.
    # ledger I109: dev net +18.4 bp/month-end (381 months), se 4.163; PASSED. Tradable IEF log, registered DGS10 numbers
    Member(
        "shelf_i109_ief",
        "shelf_i109_ief.csv",
        "period",
        "net_bp",
        "bp",
        12 / 52.1775,
        18.4,
        4.163 * math.sqrt(381),
        0.65,
        "ledger I109",
    ),
    # ledger I73 (Strategy 19): test 266 weeks net +112 bp/week, t 2.93 -> sd = 112 / 2.93 x sqrt(266); UNPROVEN-POSITIVE
    Member(
        "strategy19",
        "crypto_carry.csv",
        "entry_time",
        "net_bp",
        "bp",
        1,
        112.0,
        112.0 / 2.93 * math.sqrt(266),
        0.4,
        "ledger I73",
    ),
    # ledger I78 (Strategy 20, Monday, not liquid): dev net +145.0 bp/week (186 weeks), se 44.75; PASSED
    Member(
        "strategy20",
        "crypto_flow.csv",
        "entry_time",
        "net_bp",
        "bp",
        1,
        145.0,
        44.75 * math.sqrt(186),
        0.65,
        "ledger I78",
    ),
)


def week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _day(s) -> date:
    s = str(s)
    if len(s) == 7:  # month label (I-109): the month-end window, dated by the month's last day
        return pd.Period(s, "M").end_time.date()
    t = pd.Timestamp(s)
    return (t.tz_localize("UTC") if t.tzinfo is None else t.tz_convert("UTC")).date()


def sd_week(m: Member) -> float:
    return m.sd * math.sqrt(m.ppw)


def shrunk_sharpe(m: Member) -> float:
    return m.factor * m.mean * m.ppw / sd_week(m)


def weights(members=MEMBERS) -> dict[str, float]:
    s = {m.name: max(shrunk_sharpe(m), 0.0) for m in members}
    tot = sum(s.values())
    return {k: (v / tot if tot else 0.0) for k, v in s.items()}


def load(m: Member, folder: Path = FORWARD):
    """The member's logged periods as [(date, net)], or None when the log file is missing."""
    p = folder / m.file
    if not p.exists():
        return None
    d = pd.read_csv(p)
    return [(_day(a), float(v)) for a, v in zip(d[m.date_col], d[m.col], strict=True)]


def weekly(rows, m: Member) -> dict[date, float]:
    """Net per ISO week in registered weekly-sd units."""
    out: dict[date, float] = {}
    for d, v in rows:
        w = week_start(d)
        out[w] = out.get(w, 0.0) + v / sd_week(m)
    return out


def book(members=MEMBERS, folder: Path = FORWARD):
    """Per-member stats, weights and the weekly book series (risk units; zero-filled weeks)."""
    w = weights(members)
    per, series = {}, {}
    for m in members:
        rows = load(m, folder)
        per[m.name] = rows
        if rows:
            series[m.name] = weekly(rows, m)
    weeks = []
    if series:
        a, b = min(min(s) for s in series.values()), max(max(s) for s in series.values())
        weeks = [a + timedelta(days=7 * i) for i in range((b - a).days // 7 + 1)]
    vals = [sum(w[k] * s.get(wk, 0.0) for k, s in series.items()) for wk in weeks]
    return w, per, weeks, vals


def report(folder: Path = FORWARD, members=MEMBERS) -> str:
    w, per, _, vals = book(members, folder)
    out = ["Forward book (reporting only; correlations between members assumed 0)", ""]
    for m in members:
        rows = per[m.name]
        head = f"{m.name:15s} w {w[m.name]:.3f}  shrunk exp {m.factor * m.mean:+.3f} {m.unit}/period (x{m.factor})"
        if not rows:
            out.append(f"{head}  no rows yet")
            continue
        x = [v for _, v in rows]
        mu = sum(x) / len(x)
        z = mu / (m.sd / math.sqrt(len(x)))  # registered sd, not the forward one
        out.append(f"{head}  periods {len(x)}  fwd mean {mu:+.3f} {m.unit}  z {z:+.2f}")
    n = len(vals)
    ex = sum(w[m.name] * shrunk_sharpe(m) for m in members)  # risk units per week
    sd0 = math.sqrt(sum(v * v for v in w.values()))  # each member has weekly sd 1 in risk units
    out.append("")
    if not n:
        out.append(
            f"Book: weeks 0 (no rows yet); expected {ex:+.3f} risk units/week, sd {sd0:.3f}; "
            f"expected z = {ex / sd0:+.3f} x sqrt(weeks)"
        )
        return "\n".join(out)
    mu = sum(vals) / n
    sd = math.sqrt(sum((v - mu) ** 2 for v in vals) / (n - 1)) if n > 1 else float("nan")
    z = mu / (sd / math.sqrt(n)) if n > 1 and sd > 0 else float("nan")
    out.append(
        f"Book: weeks {n}  weekly mean {mu:+.3f} sd {sd:.3f} (risk units)  z {z:+.2f}  "
        f"expected z at shrunk mean {ex / sd0 * math.sqrt(n):+.2f}  cumulative {sum(vals):+.3f}"
    )
    return "\n".join(out)


def selfcheck() -> None:
    w = weights()
    assert abs(sum(w.values()) - 1) < 1e-12 and all(v >= 0 for v in w.values())
    assert week_start(date(2026, 11, 29)) == date(
        2026, 11, 23
    )  # a Sunday belongs to the Monday before
    print("SELFCHECK OK")


if __name__ == "__main__":
    if "--selfcheck" in sys.argv:
        selfcheck()
    elif sys.argv[1:] == ["report"]:
        print(report())
    else:
        sys.exit(__doc__)
