# Intraday structure, sessions, gaps and calendar

Sources: K = Kaufman *TSM* ch. 10, 12, 15-16, 20; H = Hougaard. All statistics are claims from the
books, mostly on 2000-2011 futures and gross of costs. Each one is a cheap study on our M1 data before
it becomes a strategy.

## Time of day
- Volume and volatility follow a **U-shape**: highest at the open, lowest at midday, rising into the
  close (open > close). Stable over 50 years (K p.689-699, 856). Compare each time bucket with its own
  history, never absolute values (K p.561).
- The **open is the most likely time for the day's high or low** (~2× the close, ~8× midday). After a
  large gap (> 2 %) the gap-side extreme is almost always at the open (K p.696-699).
- Hougaard claims 90 % of the day's extremes fall in the first 1.5 hours (unsourced) and that about
  20 % of index days are trend days (open at one extreme, close at the other), more often on Fridays
  and around month start/end (H). → I-09
- An early extreme becomes more credible as the day goes on; a break of the morning high/low after
  midday raises the odds of a close in that direction (K p.698, 749).
- S&P first 30-min bar: modest continuation in the direction of (prior close → end of bar 1) for the
  rest of the day 2000-2011, but it **reversed** in the 2009-11 bull (K p.691-696). → I-09
- EURUSD: the net gain came in the European part; highs/lows cluster at the European open; the
  London/NY overlap was flat (K p.695-697). → I-17
- Open-to-close is only about half the day's range, so a day trade can realistically capture about a
  quarter of the daily range (K p.740).

## Gaps
- 24 h markets (index CFDs, FX) have small gaps; gap rules need a defined session open (cash open
  09:30 New York for indices). Overnight gap ≈ 3-5 % of the daily range for e-mini S&P, 8-12 % for
  EURUSD (K p.701-703, 751-753).
- Small gaps (< ~0.4 %) cross the prior close > 80 % of the time; closing in the gap direction is about
  50/50 (no edge alone). Large gaps (> 1 %) continue a bit more often but also reverse more (K p.699-711).
- Hougaard: only 48 % of DAX gaps fill the same day, 76 % by day 3 (unsourced). "All gaps fill" is false.
- Classic: common gaps get faded, breakaway gaps get followed (K p.103-105; Bulkowski table garbled in
  the PDF text, re-check in the book).

## Weekday and weekend
- S&P: "up Monday, down Tuesday" reverses 54 %; most weekday patterns are 45-55 % with small samples.
  Kaufman warns that among 16 weekday branches about half deviate from 50 % by chance alone
  (K p.711-725). Use only combinations that hold under several trend filters.
- After an up week, S&P opens lower on Monday 63 % of the time; Monday closes in the prior-week
  direction 47 % (K p.723-725).
- Next-day range: higher after a high 3-day ATR; Monday lowest volatility, Tuesday/Friday highest
  (S&P 1987-95) (K p.857).

## Calendar
- **Month-end / turn of month:** buying pressure on the last ~4 and first 1-3 trading days; stronger
  2001-2011 in S&P, crude, gold. Rule: buy ~4 days before month end, exit the end of the first day of
  the new month (K p.726-729, 480). → I-18
- Pre-holiday: day before a holiday up 67.9 % (1897-1964); weaker later (K p.479-480).
- Hirsch Nov-Apr, January barometer, presidential cycle: weak or too slow for us (K p.480-494).
- Financial markets are doubtful seasonal candidates; seasonality only at monthly resolution, only
  with a physical or flow reason, and it decays (K p.483-484).
- Use seasonal / hourly volatility to scale size or skip hours where the range is small vs the spread
  (K p.453-454). → I-21

## Our context
- Session clock (`sessions.py`) gives Tokyo/London/New York opens with each city's DST; FTMO day
  resets at midnight Prague; swap at the 17:00 New York rollover.
- Day trades closed before 17:00 New York pay no swap.
- Hougaard's self-audit ("Book of Truths"): split every strategy's R by hour, weekday, Friday,
  month-end. Make this a standard report for every run. → I-22
