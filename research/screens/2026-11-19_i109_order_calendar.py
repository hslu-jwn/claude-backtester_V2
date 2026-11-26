"""I-109 hand-order calendar for CME Micro 10-Year Yield futures (prints only; places no order).

Window (card I-109, research-log 2026-11-18 venue entry): long duration over each month's last 3 Treasury trade
dates = SELL the next-month yield contract near 3 p.m. ET on the 4th-last trade date, BUY it back near 3 p.m. ET on
the month's last trade date (the front contract expires that day on the BrokerTec 3 p.m. fix).

Assumption (A1): Treasury trade dates = weekdays minus US federal holidays minus Good Friday (SIFMA's usual full
closes). SIFMA's early closes and any Good Friday exception are not modelled: check SIFMA's calendar and the broker
before each order.
Early closes (R5, lead review A file 09, 2026-11-26): SIFMA's usual 2 p.m. early closes (Thursday before Good Friday,
Friday before Memorial Day, the trade date before July 4, Christmas and New Year's Day (all as observed),
the day after Thanksgiving) are flagged; on
such a day the micro settles on the 11 a.m. fix (review A, not re-checked here), so that order goes in before 11 a.m.
ET. The flag is a pattern, not SIFMA's list: confirm each year on SIFMA's calendar.

Usage: python research/screens/2026-11-19_i109_order_calendar.py [first YYYY-MM] [months]
"""

import sys

import pandas as pd
from pandas.tseries.holiday import GoodFriday, USFederalHolidayCalendar

CODES = "FGHJKMNQUVXZ"  # CME month codes


def trade_dates(start, end):
    days = pd.bdate_range(start, end)
    hol = set(USFederalHolidayCalendar().holidays(start, end)) | set(GoodFriday.dates(start, end))
    return days[~days.isin(hol)]


def early_closes(start, end):
    """SIFMA's usual early-close pattern (see the docstring), as dates in [start, end]."""
    cal = USFederalHolidayCalendar()
    out = set()
    for y in range(start.year, end.year + 1):
        d = trade_dates(f"{y}-01-01", f"{y + 1}-01-10")
        gf = GoodFriday.dates(f"{y}-01-01", f"{y}-12-31")
        mem = list(cal.holidays(f"{y}-05-01", f"{y}-05-31"))
        jul4 = list(cal.holidays(f"{y}-07-01", f"{y}-07-07"))
        xmas_ny = list(cal.holidays(f"{y}-12-20", f"{y + 1}-01-05"))  # observed dates
        thx = [h for h in cal.holidays(f"{y}-11-01", f"{y}-11-30") if h.day > 21]
        before = [d[d < x][-1] for x in [*gf, *mem, *jul4, *xmas_ny]]  # the trade date before
        after = [d[d > x][0] for x in thx]
        out |= set(before) | set(after)
    return {x for x in out if start <= x <= end}


def rows(first, n):
    out = []
    for m in pd.period_range(first, periods=n, freq="M"):
        d = trade_dates(m.start_time, m.end_time)
        nxt = m + 1
        early = early_closes(m.start_time, m.end_time.normalize())
        flag = " ".join(
            f"{x:%m-%d} early: order before 11 am" for x in (d[-4], d[-1]) if x in early
        )
        out.append(
            (str(m), d[-4].date(), d[-1].date(), f"10Y{CODES[nxt.month - 1]}{nxt.year % 10}", flag)
        )
    return out


def main():
    first = sys.argv[1] if len(sys.argv) > 1 else pd.Timestamp.today().strftime("%Y-%m")
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 7
    print(
        "month    SELL 1 (~3 pm ET)  BUY 1 to close (~3 pm ET)  contract   (verify holidays with SIFMA / broker)"
    )
    for month, entry, exit_, contract, flag in rows(first, n):
        print(f"{month}  {entry}         {exit_}                 {contract}  {flag}")


# self-check: Nov 2026 has Thanksgiving (26th) and Veterans Day (11th, a SIFMA close too); last trade date Mon 30th
assert rows("2026-11", 1)[0][1:] == (
    pd.Timestamp("2026-11-24").date(),
    pd.Timestamp("2026-11-30").date(),
    "10YZ6",
    "",
)
# Dec 2026: Christmas Fri 25th; last trade date Thu 31st; holds the January 2027 contract
assert rows("2026-12", 1)[0][1:] == (
    pd.Timestamp("2026-12-28").date(),
    pd.Timestamp("2026-12-31").date(),
    "10YF7",
    "12-31 early: order before 11 am",
)
# 2027: Good Friday Mar 26 -> Thu 25th early (the March entry date); Memorial Day May 31 -> Fri 28th (May exit)
assert rows("2027-03", 1)[0][4] == "03-25 early: order before 11 am"
assert rows("2027-05", 1)[0][4] == "05-28 early: order before 11 am"
# 2027: New Year 2028 is observed Fri Dec 31, so Thu Dec 30 (the December exit) closes early
assert rows("2027-12", 1)[0][2:] == (
    pd.Timestamp("2027-12-30").date(),
    "10YF8",
    "12-30 early: order before 11 am",
)

if __name__ == "__main__":
    main()
