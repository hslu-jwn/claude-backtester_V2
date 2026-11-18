"""I-109 hand-order calendar for CME Micro 10-Year Yield futures (prints only; places no order).

Window (card I-109, research-log 2026-11-18 venue entry): long duration over each month's last 3 Treasury trade
dates = SELL the next-month yield contract near 3 p.m. ET on the 4th-last trade date, BUY it back near 3 p.m. ET on
the month's last trade date (the front contract expires that day on the BrokerTec 3 p.m. fix).

Assumption (A1): Treasury trade dates = weekdays minus US federal holidays minus Good Friday (SIFMA's usual full
closes). SIFMA's early closes and any Good Friday exception are not modelled: check SIFMA's calendar and the broker
before each order.

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


def rows(first, n):
    out = []
    for m in pd.period_range(first, periods=n, freq="M"):
        d = trade_dates(m.start_time, m.end_time)
        nxt = m + 1
        out.append((str(m), d[-4].date(), d[-1].date(), f"10Y{CODES[nxt.month - 1]}{nxt.year % 10}"))
    return out


def main():
    first = sys.argv[1] if len(sys.argv) > 1 else pd.Timestamp.today().strftime("%Y-%m")
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 7
    print("month    SELL 1 (~3 pm ET)  BUY 1 to close (~3 pm ET)  contract   (verify holidays with SIFMA / broker)")
    for month, entry, exit_, contract in rows(first, n):
        print(f"{month}  {entry}         {exit_}                 {contract}")


# self-check: Nov 2026 has Thanksgiving (26th) and Veterans Day (11th, a SIFMA close too); last trade date Mon 30th
assert rows("2026-11", 1)[0][1:] == (pd.Timestamp("2026-11-24").date(), pd.Timestamp("2026-11-30").date(), "10YZ6")
# Dec 2026: Christmas Fri 25th; last trade date Thu 31st; holds the January 2027 contract
assert rows("2026-12", 1)[0][1:] == (pd.Timestamp("2026-12-28").date(), pd.Timestamp("2026-12-31").date(), "10YF7")

if __name__ == "__main__":
    main()
