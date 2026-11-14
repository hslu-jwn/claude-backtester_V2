# The cost wall (read before proposing any strategy)

Synthesis 2026-11-09 of every V2 / V1 result. Sources: RL = `docs/research-log.md`, RM1 = `docs/archive/ROADMAP-v1.md`
(phase / step), TH = `docs/strategy-timed-hold.md`, AP = `docs/strategy-alternating-path.md`, CT = `knowledge/research/reports/2026-11-09_cost_in_R_table.md`,
TR = `..._m15_candidate_triage.md`, I52 = `I52_COST_LIMIT_SCREEN_METHOD_CHECK.md`. Nothing here is new data; "n/a" = not in the sources.
Per-trade values marked (d) are derived by dividing the source's totals; R = stop-defined, dev period 2015-01-02..2021-09-13 unless "2020-26"
(RM1 early strategies used 2020-2026, fixed spread). Gross - net = cost.

## 1. Every tested strategy / family

Since 2026-11-11 the per-idea record is `research/ledger.csv` (one row per idea or hypothesis); this table stays as the 2026-11-09 synthesis.

| Strategy (instrument; hold; stop) | Trades | Gross R/tr | Cost R/tr | Net R/tr | Verdict | Source |
|---|---|---|---|---|---|---|
| 1 Session zones (XAU, GBPUSD, GBPJPY; intraday; tight) | 17,742 | -0.047 (d) | 0.12 (d) | -0.166 (d) | all years, all symbols negative | RM1 Ph.7 |
| 2 NY index sweep (NAS100, US500; intraday; n/a) | 1,658 | +0.018 (d) | 0.055 (d) | -0.037 (d) | no edge | RM1 Ph.8 |
| 3 No-wick, 15m higher close (5 symbols; intraday; tight) | 23,795 | -0.033 (d) | 0.14 | -0.173 (d) | 24 of 24 variants negative gross and net | RM1 Ph.9 |
| 4 Trend following (5 symbols; days; n/a) | 1,027 | n/a (noisy tercile: -0.010 / +0.015) | swap 0.03-0.2 | -0.177 (d) | gold swap kills it; GBPJPY +0.16 detrended = 1 of 30+ cells | RL profiles; RM1 Ph.10, 11.1 |
| 5 Gap fade (NAS100, US500; open to 16:00; mirror-gap stop) | 2,374 | +0.047 (d) | 0.024 (d) | +0.023 (d) | 2020-26 weak positive; OOS 2018-19: 747 tr, gross -0.030, net -0.080 (d); walk-forward +0.6 R / 1,423 tr: no edge | RM1 11.4, 11.6, 11.7 |
| 6 ORB, dev (18 symbols; 5-30 min range; n/a) | n/a | +0.01 to +0.04 | ~0.1 (ATR bands less) | best -0.005 to -0.014 | 0 of 23 variants net positive | RM1 11.10 |
| 6 ORB, test (US indices, band 0.25 ATR, volume filter) | 301 | +0.116 (d) | 0.016 (d) | +0.10 | t ~1.5, halves +27.6 / +2.7, fading since 2024; not confirmed | RM1 11.10 |
| 7 Gap momentum (indices; to close) | 975 | +0.002 (screen N20) | n/a | -0.012 (d) | no edge | RL profiles; RM1 12.12 |
| 8 London-fix reversal (6 USD pairs; <= 180 min; 5 ATR) | 10,397 | +0.017 (d) | 0.117 (d) | -0.10 | 9 of 9 variants negative; drift real, costs eat it | RL 2026-10-28 |
| 9 R014 FOLLOW 30 / 60 min (6 FX; M15; 1 ATR) | 17,673 / 16,626 | -0.009 / -0.019 (d) | ~0.21 | -0.222 / -0.233 (d) | rejected by user 2026-11-06 | RL, AP Gates |
| 9 R014 FADE 30 / 60 min (same) | 15,160 / 14,042 | +0.021 / +0.028 (d) | ~0.21 | -0.190 / -0.184 (d) | rejected; largest gross of the M15 family | RL, AP Gates |
| 10 F1a EURUSD short 07:00-13:00 (6 h; 0.5 daily ATR) | 1,723 | +0.066 (d) | 0.023 (d) | +0.042 | best V2 cell: passes costs x2, halves, p 0.008; fails joint rule (GBPUSD -25.8 R net); 1 of 12 cells; a lead | TH Results |
| 10 F1b USD-hours long EURUSD (same) | 1,719 | +0.046 (d) | 0.024 (d) | +0.023 | fails costs x2, halves, boot, breadth | TH Results |
| 10 F2 last-30-min momentum US500 (30 min; 0.5 ATR) | 1,605 | +0.010 (d) | 0.044 (d) | -0.034 | gross +16 / +21 (NAS100) / +29 (UK100) / +36 (GER40) / +10 (EU50) R: sign right everywhere, net negative | TH Results |
| 10 F2-EU UK100 / EU50 | 1,666 / 882 | +0.017 / +0.012 (d) | 0.050 / 0.051 (d) | -0.032 / -0.039 | falsified after costs | TH Results |
| 10 F2L F2 on days with move >= 0.5 ATR (US500) | n/a | +0.008 | ~0.043 (d) | -0.035 | gross does not rise on large-move days | RL hyp. 6; TH |
| 10 F1X cross shorts EURJPY, EURAUD, GBPJPY, GBPAUD (EU hours) | ~1,720 each | +0.015 to +0.025 | 0.04-0.06 | negative on all four | sign confirmed gross, net negative | RL hyp. 7; TH |
| 10 F3 FOMC morning (US500) | 52 | -0.225 (d) | 0.046 (d) | -0.271 | falsified (opposite sign) | TH Results |
| 10 F4 turn of month, open to close (US500) | 315 | -0.013 (d) | 0.046 (d) | -0.059 | no effect | TH Results |
| Study 11.2 gap fill 0.1-1 ATR (NAS100, US500; 1:1) | study | +0.04-0.05 | "large share" | see strategy 5 | fill-first 44 vs 37 %: tiny excess over random-walk touch | RM1 11.2 |
| Study 11.1 noise (5 symbols, M15-D1) | study | -0.010 noisy third / +0.015 others (strategy 4) | ~0.1 fast TFs | n/a | all markets near random-walk ER; ER gate cannot rescue | RM1 11.1 |
| Study 11.11 / T-11 stationarity (21 symbols) | study | next-hour reversal 0.2-0.5 spread | 1 spread | negative | 0 of 105 ADF; reversal real but tiny, not tradeable | RM1 11.11 |
| Study 11.13 / I-61 H1 shock (21 symbols) | study | NAS100 H1 k4 h2 +0.20 sd trimmed (t 1.74), halves +0.65 / +0.23 | n/a | n/a | 2 findings, both reversals, not tradeable; rest = top 1 % crash / news hours | RM1 11.13 |
| 18 M15 drafts (R007-R024, 6 FX, 1-2 ATR) | not run | none supported (R014: +0.025) | 0.2 at 1 ATR, 0.1 at 2 ATR | n/a | 0 built: 12 duplicate failed families, rest COST_INFEASIBLE | TR |
| 14 US close -> German open (GER40, US500 signal; 2026-11-12) | 598 | +0.015 | ~0.022 | -0.008 | falsified; UK100 breadth -39 R | L14 |
| L15-L18 lead-lag screens (oil->CAD, USD breadth, gold->silver, BTC->ETH) | 387-656 | bp: +1.2 / -0.9 / +3.7 / -19.6 | bp: 1.7 / 1.6 / 15.5 / 13.1 | all negative | screens, not built | ledger L15-L18 |
| I-51 trend portfolio, 35 symbols, monthly (2016-2021) | 67 months | gross Sharpe -0.13 | swap -1,924 bp, spread -32 bp total | Sharpe -1.03 | killed; swap alone sinks a real trend edge | ledger I51 |
| I-67 / I-69 / I-70 calendar (month-end sign, BTC expiry week, opex week) | 80 / 41 / 129 | bp: +19.9 / -60 / +8.7 | bp: ~6 / ~40 / ~12 | +14 / -100 / -4 | killed (t < 2 / none / none) | ledger |
| H13f CAP reversal, pre-sample + development | 50 | n/a | n/a | +0.136 R mean | killed: < 80 trades, bootstrap <= 0 | ledger H13f |

## 2. The pattern

- Gross edge per trade is between -0.05 and +0.07 R in every test, and the positive values are small: +0.01 to +0.03 R at M15 / session-intraday
  stops (R014 FADE, F2, F1X, strategy 2, ORB dev), +0.04-0.07 R only for 6-hour or open-to-close holds (F1a, F1b, gap fade in-sample, ORB test).
- Cost per trade scales with the stop: 0.10-0.14 R at tight 5-30 min stops (strategies 1, 3, 6, 8), ~0.2 R at a 1-ATR M15 stop (CT: 0.07-0.69 R by symbol),
  0.04-0.05 R at a 0.5 daily-ATR stop on indices (F2), 0.02 R on EURUSD at the same stop (F1a).
- A positive net exists in exactly two places: EURUSD 6 h short (+0.042 R, 1 of 12 cells, GBPUSD disagrees) and the weak, non-replicating index cells
  (gap fade 2020-26, ORB test). Both are leads or fading, not edges.
- Where the sign was predicted by a published paper it showed up gross almost everywhere (F2 in 5 of 5 indices, F1X in 4 of 4 crosses, London fix 4 of 6 pairs,
  R014 FADE) but is 0.01-0.03 R, below cost. The effects are real and too small for retail CFD costs. 0 of ~25 cells beyond F1a are net positive and robust.

## 3. The arithmetic

- Cost in R = round-trip cost (spread + 2 x slippage + commission, price) / stop distance (CT). Stop-outs pay slippage twice.
- A wider stop does not help if the effect scales with the stop: gross R per trade = drift / stop, cost R = cost / stop, so net/gross ratio is unchanged
  (TR finding 1: 2-ATR stop halves cost to 0.1 R but halves the gross R of a given drift too). Stop width only changes the unit.
- It does help when the effect (a) is a price move in bp that does not shrink with a larger stop, i.e. the stop is non-binding and the exit is a timer
  (timed_hold: cost 0.2 R at 1-ATR M15 -> 0.02-0.04 R at 0.5 daily ATR), and (b) grows with holding time while cost stays fixed per round trip
  (F1a 6 h +0.066 R gross vs F2 30 min +0.010 R). Longer holds are limited by swap (any hold past 17:00 New York) and by decay of the effect.
- Break-even win rate with stop S, target T, cost C: (S + C) / (S + T) (I52). At S = T and C/T = 0.10, 50 % becomes 55 %.
- FTMO pass map (2026-11-14, `knowledge/research/reports/2026-11-14_challenge_pass_map.md`): zero net edge passes
  ~30 % by luck; +0.05 R net needs ~340 trades at 0.5 % risk for 64 % (+0.10 R: 89 % in ~260); below +0.02 R net
  the pass chance is within ~10 points of luck. Required size for a goal-1 build: ~+0.05 R net, ~300+ trades a year.
- Turnover: 2,000 trades/yr x 0.2 R = ~400 R/yr drag (TR). Fewer trades cost less in total, not per trade; no feasibility without gross edge.
- Cost table at a 0.5 daily-ATR stop (CT, last column): US30 0.013, EURUSD 0.022, NAS100 0.022, GER40 0.016, USDJPY 0.032, US500 0.038, XAUUSD 0.038, UK100 0.044,
  GBPJPY 0.065, USOIL 0.103, XAGUSD 0.143. At 1-ATR M15: NAS100 0.128, US30 0.072, GER40 0.074, EURUSD 0.108, others 0.17-0.69.
- **Since 2026-11-13** (hourly table for 32 symbols, live factors, bar-close lookup): the 0.5-ATR column scaled by the dev-period
  cost ratio (London / NY hours, each year's own price; `research-log.md` 2026-11-13): US30 0.010, GER40 0.012, NAS100 0.023,
  EURUSD 0.027, UK100 0.030, XAUUSD 0.038, US500 0.040, USDJPY 0.042, GBPJPY 0.069, USOIL 0.072, XAGUSD 0.279. Cheapest now:
  US30, GER40, NAS100; EURUSD / USDJPY dearer (2015-19 spreads 2-4x today's), XAGUSD about double. Hour 17 New York (rollover)
  is 9-20x on FX: any exit or entry there pays it.

## 4. Implications for idea selection

- A net-positive idea needs gross R per trade clearly above the cost in its own cell: >= ~0.05 R gross on EURUSD / US30 / GER40 / NAS100 session stops,
  >= ~0.10 R elsewhere. Compute the cost first (I52 rule: report cost burden, never a pass certificate; passing = COST_FEASIBLE_UNKNOWN_EDGE).
- Effects that could clear it: session-length holds (hours) on the cheapest symbols with a published bp effect; event-conditioned trades where the
  per-trade move is large (published 20-35 bp per event) and counts are low; effects that grow with holding time; none yet verified post-2015 on our data.
- Stop proposing: any M15 / H1 bar-pattern, path, oscillator, MA-cross or candle-geometry rule at stops under ~1 daily ATR (families A-E in TR, no-wick,
  session sweep, R014 variants, round numbers, wick rejection, indicator filters); gap fade and gap momentum (no OOS edge); ORB without a new mechanism;
  H1 shock continuation or reversal (I-61); FX relative-strength / basket rules (highest turnover, 0.2 R per leg); pre-holiday, day-of-week, pre-FOMC
  drift post-2015, macro-day long, pre-ECB, gold session rules, Tokyo / London fix reversals, generic option-expiry
  (I-70 re-tested it anyway on 2026-11-12 despite this line: killed again); daily lead-lag across markets
  (L14-L18); diversified or single-symbol trend at any speed (I-51, strategy 4); month-end / turn-of-month in
  any form (F4, F4M, I-67); daily reversal E8 / CAP / TS; multi-day holds on crypto CFDs (-30 %/yr swap,
  ~8 bp a night) and multi-week holds anywhere unless the published edge is several times the swap.
- Tuning stop, hold, signal frequency until the screen passes creates a new family and adds multiplicity (I52). Reversing a failed signal does not rescue it
  (strategy 3 and 1 reversed are no better).
- Live leads (2026-11-12): none. F1a EURUSD European-hours short failed its 2008-2014 pre-sample check
  (closed 2026-11-11); last-30-minute momentum did not rise above 0.05 R gross; NAS100 H1 shock decayed.
  Every look on 2026-11-12 (strategy 14, L15-L18, I-51, I-67, I-69, I-70, H13f) was killed.

## 5. Open data issues that bias costs or results

- ~~Spread model is a lower bound for 2015-2019~~ fixed 2026-11-13: the hour / year table covers 32 symbols (MT5 history, from 2015 or
  the symbol's first MT5 year; BTCUSD / ETHUSD keep the fixed spread). 2020-21 of seven FX symbols are a 50-point placeholder in the feed
  and take 2019 / 2022 values; GBPUSD's placeholder cells (below) remain.
- GBPUSD table values 2020-21 NY hours 0-12 are ~5x other years (likely a median artefact, not corrected, CT).
- Live spreads 2026-11-09 (7,019 fills, 23 symbols, ~4.6 days, RL): FX medians match the model, means 1.4-2x from Asia / rollover bars (NY hour 18 ~5x).
  Under-charged by mean: GBPJPY 2.25x, GBPUSD 1.97x, NAS100 1.95x, UK100 1.77x, XAUUSD 1.63x, GER40 1.52x; BTCUSD slippage 5x. EURUSD median 0,
  slippage 0.81x: F1a not flattered. Index results (F2) are therefore if anything too kind. The proposal's raises were applied on 2026-11-09 (`d0bbcd8`, fixed spreads) and the table scaled on 2026-11-11 (review B1).
- Short live sample (4.6 days, one week-regime); costs under stress (news, thin hours) can be much higher (p90 UK100 5.1 vs 1.45).
- Histdata gaps: GER40 ends 2020-06-12, EU50 ends 2018-12-14, US30 only from 2019-02-10 (MT5), USOIL 205 MT5 days; US500 histdata omits quiet minutes
  (2017 worst, median 23 missing/day) and the strict integrity gate over-flags (808 of 1,669 trades in the baseline, 78 with a 5-min tolerance); 556 of 882 EU50 trades
  touch a missing candle; 39 index trades exit after rollover on holiday / early-close days (TH). Index 2023-02..07 has hour-sized holes (RM1 11.2).
- Data and stop caveats: XAGUSD was ~-1 R/trade in ORB because a 2026 spread sits on 2015 prices (RM1 11.10); the spread is also a larger share of the stop where
  stops are small (gap fade slippage stress). Net R in early strategies (RM1) used engine slippage not yet applied (RM1 12.8), so they are optimistic.
- Multiplicity: the timed-hold program is 7 hypotheses / 16 cells (family level 0.01); F1a's p 0.008 is 1 of 12 cells at registration, not an isolated test.
