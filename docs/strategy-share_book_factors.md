# Share book factors: low idiosyncratic vol, 12-1 momentum, year-end tax-loss (I-129, I-130)

Built on the user's word (2026-11-19, "use the same framework to build the strategies and test them") although the
cards were PARKED on power (M4): the power line below stays, so a failure is read as "not detectable here", not as
"no effect". Venue M13 real US shares (long-short). Written before any data look (cards I-129 / I-130 in
`knowledge/ideas.md`). I-131 (fund fire sales) is not built: no free fund-flow data.

## Common frame (as I-101, `research/screens/2026-11-17_i101_short_volume_screen.py`)

- Universe: `data/cache/alpaca_meta/universe.csv`, the month's top 1,000 by dollar volume (point in time, delisted
  names kept; `docs/share-universe.md`). Prices: Alpaca daily closes, split-adjusted (`data/cache/alpaca_1d`).
- Holding: monthly. Entry at the close of the month's first trade date, exit at the close of the next month's first
  trade date (A2 of I-101: no exit bar -> last close, a delisting holds its last price).
- Signals use only closes up to and including the entry date's previous trade date (no lookahead).
- Cost per month (A1): 2 legs x 2 fills x (2 bp fee + 1 bp slippage) = 12 bp + borrow on the short leg
  ~0.6 bp a week = 2.6 bp: **COST = 15 bp a month** on the long-short spread (equal weight inside each leg).
- Periods: development 2016-05 .. 2021-08 holding months (entries before 2021-09-14); one-time test 2021-09 .. the
  last complete month, only for a cell that passes every development gate (Mode=auto runs it).

## Hypotheses (4 counted rows, one family each)

- **H1 `share_low_idio_vol` (I-129, AHXZ 2006 via AM p.334):** idio vol = sd of the residuals of a daily OLS of the
  stock's return on SPY's over the previous calendar month (>= 15 common days, else dropped). Quintiles; long the
  lowest, short the highest. Published -1.06 % a month (high minus low, 1963-2000); halved: +0.53 % long-short.
- **H2 `share_momentum` (Clenow SOTM / Jegadeesh-Titman):** return from the close 12 months before the entry to the
  close 1 month before (skip the last month); >= 200 closes. Deciles; long the top, short the bottom.
- **H3 `share_tax_loss` loser basket (I-130, STA p.116):** event per December: names in the universe whose close on
  the trade date before the event date (the first trade date on or after 15 Dec) is within 2 % of their 252-day low
  close up to that day (A5: selection strictly before the entry); buy the event date's close, sell the close of
  the first trade date on or after 15 Feb; excess = basket mean minus the universe equal-weight mean over the same
  dates. Cost 12 bp (no short leg; the benchmark is a measurement, not a trade). Development Decembers 2016-2020.
- **H4 `share_tax_loss` small-cap December (I-130, STA p.112):** IWM minus IWB, close of the 11th December trade
  date to the close of December's last trade date. Cost 4 bp. Development Decembers 2016-2020.

## Gates (fixed now; a cell passes only if no kill is hit)

- |t| of the net mean >= 3.3 (M9, two-sided), and the sign as registered (H1 long low IV, H2 long winners, H3 / H4
  long the loser / small-cap leg); net mean > 0; both halves > 0 (H1 / H2: holding months 2016-2018 vs 2019-2021;
  H3 / H4: Decembers 2016-2017 vs 2018-2020); doubled cost > 0; without the 2 best periods > 0.
- Negative control (power): the same sort with labels shuffled within each month, 200 draws: report the sd and the
  share of |t| >= 3.3 (must be <= 5 %).
- Reported, not gated: decile / quintile means, years, the spread capped at +-50 % per name, beta of the spread to SPY.

## Power (M4, written before the run)

- H1 / H2: ~64 development months; monthly long-short sd ~4-5 %: se ~0.55 %; t 3.3 needs ~1.8 % a month net; the
  halved published sizes are ~0.5 % (H1) and ~0.6 % (H2): expected t ~1, pass chance < 5 %.
- H3 / H4: 5 events; even the full published sizes give expected t < 1.5: pass chance ~0.
- Causal check (T-21): mechanisms and confounders as on the cards; the named placebo is the shuffled-label control.

## Assumptions (Opus)

- A1 cost as above (I-101 per-leg fills, monthly turnover taken as full).
- A2 CAPM residual on SPY instead of FF3 (no free daily factors in the repo); equal weights (no market caps).
- A3 monthly IV formation and holding (AHXZ's main table) instead of AM's quarterly wording.
- A4 a name needs a close on the entry date; missing exit closes use the last close (I-101 A2).
- A6 H3: a December with no name within 2 % of its low is no trade (skipped, reported); seen in the run before any
  return was printed (Dec 2020 empty).
- A5 H3 selects on the previous trade date's close (Codex flagged the same-close conflict before any data look).
