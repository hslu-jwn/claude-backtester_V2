# Intraday structure, sessions, gaps and calendar

Sources: K = Kaufman *TSM* ch. 10, 12, 15-16, 20; H = Hougaard; EC = Chan ch.3-4, 7; KD = Davey; RC = Carver; JK = Kaeppel. All statistics are claims from the
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

## From the day-trading books
- **Aziz (US stocks):** the open 9:30-11:00 New York is the best window (most size); midday 11:00-15:00
  the worst; the last hour trends with the professionals. Wait 10-15 min after the open before VWAP
  trades; the first 5 minutes are chaos. Flat before the close. → I-22 (split R by these windows)
- **Previous-close magnet (Aziz "red-to-green"):** on gap days price is drawn toward the prior close;
  enter from the session mean or a level, target the prior close. On index CFDs the "gap" is the
  09:30 open vs the 16:00 New York close of the cash session. → I-39, linked to I-09
- **Volman (EURUSD):** the Asian session prints long, clean ranges (2 h or more); the US lunch hour forms
  readable ranges around round numbers that often break when traders return; avoid major releases (NFP,
  rate decisions): bars print 10x faster, levels evaporate, spreads widen.
- **Coulling:** the first bar at the cash open on low volume is often a probe ("trap"); in 24 h FX the
  open equals the previous close, so FX has no gap signal.

## Gap momentum and time-of-day reversion (Chan, ch.3-4, 7)
Sources: EC p.63, 93-96, 155-168. Ideas I-46 (gap momentum), I-17 (time of day), I-39 (gap fade, no edge). All numbers are **gross of costs**
and in-sample (his words).
- **Opening-gap momentum:** buy if today's open is above yesterday's **high** by entryZscore × the sd of daily close-to-close returns (90-day,
  entryZscore **0.1**, a tiny threshold); short if the open is below yesterday's **low** by the same margin; exit at the close (open-to-close
  return). Eurostoxx 50 future: APR 13 %, Sharpe 1.4 (2004-12). The same rule on GBPUSD with the day defined from 17:00 New York (close) to
  05:00 New York (London open): APR 7.2 %, Sharpe 1.3 (2007-12) (EC p.155-157). Rationale: stop orders cluster beyond the prior extreme and cascade
  after a long closed period, plus overnight news. On a 24 h FX market the only real gap is the weekend one, so signal counts are low.
- This is the **opposite direction** of the gap fade (strategy 5 / I-39, which found no edge): it needs a gap *beyond the previous high / low*, not
  just away from the previous close. Chan's stock buy-on-gap is the reversion side for moderate gaps with a trend filter (price above its 20-day MA),
  so the split by gap size, by "beyond prior range" and by trend filter is the question to measure (study with I-09).
- A VIX above 35 cut the Eurostoxx gap rule from Sharpe 1.4 to 0.16 (EC p.184); the sign of such a switch is strategy specific.
- **Post-earnings drift** (stocks): trade the open in the direction of the gap if |gap| ≥ 0.5 sd; the drift horizon has shrunk to intraday and
  overnight holding was negative. **Leveraged-ETF rebalancing:** momentum in the last 15 min after a move above 2 % (DRN Sharpe 1.8). Macro
  releases on EURUSD showed no momentum in his test (EC p.158-164). Not applicable to our data except as an index last-hour check.
- Time-of-day: reversion can exist only in particular parts of the day (open to close for the gap-down stocks); bucket returns and
  autocorrelation by half-hour per symbol and per half-sample, trade only buckets with a stable sign (EC p.63, 96). → I-17

## Session structure from the practitioner books
- Davey: keep one session definition across the whole history; both euro systems are flat by a fixed time (07:00 and 15:00 ET), skip the thin
  15:00-17:00 window, one trade a day for the day system; day trading is attractive but 9 of 10 short-timeframe ideas fail (KD ch.10, 18).
- Carver: intraday trading needs near-zero costs ([costs-and-execution.md](costs-and-execution.md)); seasonality appears only as forced-trader
  effects such as tax-year end (RC ch.2).
- Kaeppel: a market-on-open order after a gap fills far from the plan (JK p.114-115).
