# F1a EURUSD dissection (descriptive robustness check, 2026-11-09)

Scope: development data only, 2015-01-02..2021-09-13. Trades: stop 0.5 ATR cell of
`timed_hold_fx_eu_bc50a92b` (v0000, EURUSD rows only, 1,723 trades, +72.5 R net / +112.9 gross) and
`timed_hold_fx_us_bd62db2b` (F1b, EURUSD, 1,719 trades, +39.5 net / +79.9 gross). Nothing here is a
rule or a proposed filter; the slices are read-outs of a result already fixed. Many slices are
shown, so single cells (a weekday, a month) are exposed to chance and must not be read as findings.
Script: `scratchpad/f1a/f1a_dissect.py` (not in the repo). Year / weekday / month use the London
entry date.

## 1. Calendar slices (R, net of normal costs)

| Year | F1a n | F1a gross | F1a net | F1a net/trade | F1b net |
|---|---|---|---|---|---|
| 2015 | 245 | 18.7 | 14.9 | 0.061 | 18.2 |
| 2016 | 260 | 18.9 | 13.2 | 0.051 | 5.6 |
| 2017 | 259 | 26.0 | 19.7 | 0.076 | 41.3 |
| 2018 | 260 | 19.0 | 12.9 | 0.049 | -13.4 |
| 2019 | 259 | 15.7 | 9.3 | 0.036 | -5.2 |
| 2020 | 260 | 4.4 | -2.2 | -0.008 | -7.5 |
| 2021 (to 09-13) | 180 | 10.2 | 4.6 | 0.026 | 0.5 |

Positive years: F1a 6 of 7 (every year except 2020); F1b 4 of 7. F1a net/trade falls from 0.04-0.08
(2015-2018) to 0.036, -0.008, 0.026 (2019-2021).

| Weekday | F1a n | F1a gross | F1a net | F1b net |
|---|---|---|---|---|
| Mon | 342 | 15.1 | 7.0 | 21.0 |
| Tue | 345 | 19.3 | 11.1 | 1.5 |
| Wed | 345 | 48.5 | 40.3 | 23.9 |
| Thu | 347 | 3.7 | -4.5 | -15.4 |
| Fri | 344 | 26.4 | 18.4 | 8.5 |

| Month | F1a n | F1a gross | F1a net | F1b net |
|---|---|---|---|---|
| Jan | 135 | 16.3 | 13.1 | 2.7 |
| Feb | 141 | 16.0 | 12.7 | -2.9 |
| Mar | 156 | 22.3 | 18.9 | 19.3 |
| Apr | 150 | 5.3 | 1.9 | 6.0 |
| May | 153 | 3.6 | 0.0 | -7.3 |
| Jun | 151 | 8.5 | 5.0 | 11.4 |
| Jul | 155 | 10.2 | 6.6 | 14.8 |
| Aug | 155 | 1.8 | -2.0 | -3.5 |
| Sep | 137 | 8.2 | 5.0 | 0.1 |
| Oct | 132 | 0.9 | -2.3 | -5.9 |
| Nov | 128 | 15.8 | 12.7 | -6.2 |
| Dec | 130 | 4.1 | 1.0 | 10.9 |

Reading: F1a is positive gross in all 12 months and net in 9 of 12; Jan, Feb, Mar and Nov carry
57.3 R (79 % of net). Wednesday alone is 40.3 R (56 % of net) and Thursday is negative. F1b's
months and weekdays do not line up with F1a's (Mar is the only shared strong month).

## 2. Exit reasons and trade distribution

| | F1a n | F1a mean net | F1a sum net | F1b n | F1b mean net | F1b sum net |
|---|---|---|---|---|---|---|
| time exit | 1,456 (84.5 %) | +0.237 | +344.4 | 1,319 | +0.341 | +449.8 |
| stop loss | 267 (15.5 %) | -1.018 | -271.9 | 400 (23.3 %) | -1.026 | -410.3 |

Mean gross R of the stopped trades is -0.995 (F1a), so costs add about 0.02 R per stop. The result is
the small excess of a ~0.24 R time-exit win over a ~1.02 R stop loss at 84.5 % / 15.5 %; a
stop-hit rate of 17 % instead of 15.5 % would remove most of the net.

Net R per trade: F1a median +0.035, skew +0.62, percentiles 1 / 5 / 95 / 99 = -1.02 / -1.02 / +1.23 /
+1.87. F1b median -0.048, skew +1.36, 99th percentile +2.45.

| Share of total net | F1a | F1b |
|---|---|---|
| top 1 % of trades (17) | +41.9 R = 58 % | +61.1 R = 155 % |
| top 5 % of trades (86 / 85) | +145.7 R = 201 % | +192.1 R = 486 % |
| bottom 1 % (17) | -17.5 R | -18.5 R |
| bottom 5 % | -88.0 R | -88.6 R |

Because the losing side is capped at about -1 R by the stop, the sum is always carried by a minority
of larger time-exit wins; for F1a the top 17 trades are 58 % of net, but removing them leaves +30.6 R
(positive). Removing the top 5 % leaves -73 R, i.e. the effect is the right tail of the time exits,
not an even drip.

## 3. DST regimes (London vs New York offset differs from 5 h: about 3 weeks in March, 1 week around late Oct / early Nov)

| Regime | F1a n | F1a gross | F1a net | net/trade | F1b n | F1b net | F1b net/trade |
|---|---|---|---|---|---|---|---|
| aligned | 1,609 | 91.2 | 53.3 | 0.033 | 1,605 | 35.1 | 0.022 |
| mismatch weeks | 114 | 21.7 | 19.2 | 0.168 | 114 | 4.4 | 0.038 |

6.6 % of F1a trades make 26 % of its net, at five times the per-trade mean. (Part of the Mar / Nov
strength in section 1 is this overlap.) With 114 trades the per-trade standard error is roughly 0.06
R, so it is suggestive only; the aligned weeks alone are still +53.3 R.

## 4. Event days (data/news/economic_events.csv, impact High, EUR or USD, event inside entry..exit)

Coverage of the file begins 2020-01-02, so only 2020 and 2021 (440 F1a trades) can be sliced; 2015-2019
(1,283 trades) is not covered. 2,288 High EUR/USD events in the whole file.

| Window | n | gross | net | net/trade |
|---|---|---|---|---|
| F1a 07-13 London, event inside | 56 | 6.3 | 4.8 | 0.086 |
| F1a, no event | 384 | 8.2 | -2.4 | -0.006 |
| (F1a, EUR only / USD only / both) | 49 / 4 / 3 | | 0.9 / -0.8 / 4.8 | 3 both-currency days average +1.58 R |
| F1b 13-20:30 London, event inside | 179 | 5.0 | 0.1 | 0.000 |
| F1b, no event | 260 | 0.1 | -7.1 | -0.027 |

In the two covered years F1a's whole small positive (+2.4 R) is on event days, mostly three days
with both a EUR and a USD release; non-event days are flat to slightly negative. Sample is tiny
(56 event trades) and cannot say anything about 2015-2019.

## 5. F1a and F1b on the same dates

1,719 shared dates: Pearson correlation of daily net R 0.003, rank correlation 0.000, gross 0.003; the
two legs have the same sign on 49.9 % of dates (coin flip). They do not look like one daily reversal:
what F1a earns says nothing about F1b the same day.

| Year | F1a net | F1b net | both legs |
|---|---|---|---|
| 2015 | 14.9 | 18.2 | 33.1 |
| 2016 | 13.2 | 5.6 | 18.9 |
| 2017 | 19.7 | 41.3 | 60.9 |
| 2018 | 12.9 | -13.4 | -0.5 |
| 2019 | 9.3 | -5.2 | 4.1 |
| 2020 | -2.2 | -7.5 | -9.7 |
| 2021 | 4.6 | 0.5 | 5.1 |
| total | 72.5 | 39.5 | 112.0 |

Both legs: positive in 5 of 7 years; 2017 alone is 54 % of the combined total, 2015-2017 alone exceed the total (112.9 R).
Gross both legs 192.8 R, costs 80.8 R.

## 6. EURUSD drift per year vs F1a (first open of the year to last close, bid, pips)

| Year | EURUSD drift | F1a net | F1a gross | F1b net |
|---|---|---|---|---|
| 2015 | -1,232 | 14.9 | 18.7 | 18.2 |
| 2016 | -348 | 13.2 | 18.9 | 5.6 |
| 2017 | +1,485 | 19.7 | 26.0 | 41.3 |
| 2018 | -539 | 12.9 | 19.0 | -13.4 |
| 2019 | -252 | 9.3 | 15.7 | -5.2 |
| 2020 | +1,003 | -2.2 | 4.4 | -7.5 |
| 2021 (to 09-13) | -430 | 4.6 | 10.2 | 0.5 |

EURUSD fell in 5 of 7 years and F1a is a short, so a trend component is possible at first glance, but
F1a is also strongly positive in 2017 (+1,485 pips, an up year) and weakest in 2020 (also up). Pearson
correlation of yearly drift and F1a net is -0.10 over 7 points (F1b: +0.37); the 2017 result suggests
it is not just trend. Seven points cannot settle it; an entry-to-exit comparison against a
random-time short control was not part of this check.

## 7. Verdict on fragility

- Over time: spread across 2015-2019 (6 of 7 years positive, none above 27 % of the total; 2017 is the
  best year at 19.7 R, and without it +52.8 R remain), but fading: 2020-2021 together are only +2.4 R
  net (+14.6 gross), against +70.1 R in 2015-2019. This matches the weaker second half (+56.4 / +16.0).
  The honest reading is "real-looking in the first five years, close to nothing since 2020".
- Within the calendar: moderately concentrated. Wednesday = 56 %, four months = 79 %, DST-mismatch
  weeks = 26 % of net (6.6 % of trades), and Thursday is negative. These are post-hoc slices and,
  given the number of slices, partly chance.
- In the trade distribution: thin edge. +0.042 R per trade results from 15.5 % stops at -1.02 R
  against 84.5 % time exits at +0.24 R; costs are 40 R of the 113 gross, so a small cost or
  stop-rate change moves the sign. The top 5 % of trades exceed the whole net.
- Independence: F1b adds almost no confirmation (correlation 0, mixed years, fails its own gates), so
  F1a stands on one pair and one rule; GBPUSD gross agrees, net does not (previous result).
- Result stays what the gates said: a lead from one of 12 cells, not a pass. This dissection did
  not use the test period (nothing after 2021-09-13 was read).
