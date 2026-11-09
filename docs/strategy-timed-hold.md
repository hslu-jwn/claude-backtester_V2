# Strategy 10: Timed hold (published time-of-day and calendar effects)

Research run 1 of `Continue.Research` (2026-11-09). Folder `strategy/timed_hold/`, config
`TimedHoldConfig`, registry name `timed_hold`. Enter at a fixed clock time, hold in a fixed
direction, leave at a fixed clock time the same day or after a configured number of trading
days; a wide stop in daily ATR.

Why this shape: our own cost table (`knowledge/research/reports/2026-11-09_cost_in_R_table.md`)
shows a round trip costs about 0.2 R at a 1-ATR M15 stop but only 0.02-0.04 R at a stop of half a
daily ATR. Every intraday signal we built (strategies 1-9, R014) had a gross edge of a few
hundredths of an R at M15 stops. Published effects of a few basis points per session can only pay
their costs with session-sized stops. This strategy is one engine for several **pre-registered
hypothesis families** (section Families); each family names its source, its prediction and its
gates before any run. It does not search for windows: entry and exit times come from the papers.

## Definitions

Base timeframe **1m**. Times are local clock times in ⚙️ `zone` (DST via `zoneinfo`).

- **RSI direction:** `direction = "rsi"` selects Hypothesis 10; the default direction remains
  `"long"`. `rsi_period` (positive integer, default 2) uses Wilder smoothing on regular
  ATR-session closes (`atr_zone` / `atr_open` / `atr_close`, as `SessionStats.prev_close`),
  plus the entry candle's close as today's close. Seed with the simple mean of the first
  `rsi_period` gains and losses; subsequent averages use Wilder's recurrence. No signal until
  `rsi_period + 1` closes exist. All-equal closes: no signal (Opus 2026-11-09).
  Finished closes are retained in a bounded strategy-local deque;
  smoothing state advances once per regular session, including while a position is open.
- **RSI thresholds:** `rsi_long_below` (default 10.0) admits longs strictly below it;
  `rsi_short_above` (default 90.0) admits shorts strictly above it. Both range from 0 to 100;
  zero disables the respective side (so `rsi_short_above = 0` is long only). Equality gives no
  signal. Hypothesis 10 uses entry at `atr_close`, when today's signal close is known.
- **SMA filter:** `sma_filter_days` (non-negative integer, default 0 = disabled). In RSI mode,
  positive values require the last `sma_filter_days` regular daily closes **including the
  signal close**: longs require that close strictly above their simple mean, shorts strictly
  below. No trade before enough closes exist. Defaults leave existing directions unchanged.

- **Entry candle:** the 1m candle that **closes** at ⚙️ `entry_time` on a qualifying day. Entry at
  its close (known at that time, no lookahead). If that candle is missing, no trade that day.
- **Hold days:** `hold_days` (integer, default 0). Zero preserves the same-day rule and requires
  `exit_time > entry_time`. A positive value schedules the exit `hold_days` trading days after
  the entry date (entry date = day zero), and allows `exit_time <= entry_time`. Missing candles
  or entire missing sessions do not change the calendar target; exit at the first candle closing
  at or after that target date and time.
- **Trading calendar:** `trading_days` (default `"weekdays"`): Monday-Friday, or `"nyse"`:
  Monday-Friday minus full closures in `calendars/nyse_holidays.csv`. Early closes count as
  trading days. This calendar governs `hold_days` and `month_day`; the existing `turn_of_month`
  and `pre_holiday` filters retain their NYSE calendar.
- **Month day:** `month_day` (integer, default 0), used by `day_filter = "month_day"` and required
  to be non-zero for that filter. Positive counts from the month's first trading day (1 = first,
  8 = eighth); negative counts from its last (-1 = last, -4 = fourth-to-last). An ordinal outside
  the month's trading days qualifies no date.
- **Daily ATR:** Wilder ATR(⚙️ `atr_period`, default 14) over daily sessions of the ⚙️ `atr_zone`
  clock: candles closing in (⚙️ `atr_open`, ⚙️ `atr_close`] of one local date, built with
  `strategy/session_stats.SessionStats` (regular = a last candle within ⚙️ `atr_close_tolerance_min`
  minutes of `atr_close`). The value used is the one of the sessions **finished** before the entry
  candle closes; a session still in progress never counts. No trade until the ATR exists.
  Defaults: indices `America/New_York` 09:30-16:00; FX / metals `UTC` 00:00-23:59 with tolerance 30.
- **Qualifying day** (⚙️ `day_filter`, the local date of the entry candle in `zone`):
  - `all`: every day with an entry candle (the baseline of every family);
  - `fomc`: a scheduled FOMC statement day (`calendars/fomc_statements.csv`, scheduled = true);
  - `turn_of_month`: the last trading day of a month and the first ⚙️ `tom_days_after` (default 3)
    trading days of the next one; trading days = Monday-Friday that are not a full NYSE closure
    (`calendars/nyse_holidays.csv`);
  - `pre_holiday`: the last trading day before a full NYSE closure that falls on a weekday;
  - `month_day`: the trading-day ordinal selected by `month_day`, using `trading_days`;
  - `gotobi`: the Tokyo business day on or immediately before each month's 5th, 10th, 15th,
    20th, 25th and last calendar day, independently of `trading_days` (see Hypothesis 11).
  The calendars are published in advance (scheduled meetings, exchange holiday rules), so using
  them at the entry time is not lookahead. Unscheduled FOMC actions are excluded.

- **Skip NYSE short days:** `skip_nyse_short_days` (default false) excludes entry dates that
  are NYSE full closures or 13:00 early closes, with any `day_filter` (the user, 2026-11-09).

## Rule

- **Direction:** ⚙️ `direction` = `long` or `short` (one code path by `Direction`), or
  `with_day` / `against_day`: long when the entry candle's close is above the close of the last
  finished regular ATR session (short when below, no trade when equal or unknown); `against_day`
  the opposite.
- **Stop:** entry ∓ ⚙️ `stop_atr` × daily ATR (long: below). No take profit.
- **Time exit:** a trade still open at ⚙️ `exit_time` closes at the close of the candle closing at
  that time on the target date, or at the first later candle if it is missing. With `hold_days = 0`,
  the target is the entry date and `exit_time` must be after `entry_time`. Multi-day scheduling
  stays inside `timed_hold`; shared `session_stats.TimedExit` is unchanged.
- One trade per day at most. A multi-day position blocks new entries until it is closed or its
  order is skipped; the candle queuing its time exit cannot open another position. Position state
  belongs to each strategy instance. SL inside a candle: engine rules (SL first).

## Families (pre-registered 2026-11-09, before any run)

From the literature reports in `knowledge/research/reports/2026-11-09_*.md` (sources marked opened
in full / abstract only there). Every number below is the papers', gross, on their samples; none
is ours. 4 families, 5 hypotheses, 12 grid cells. Primary cell = the first stop value listed.

| Family | Source and prior | Rule (zone, entry -> exit, direction) | Symbols (primary first) | Cells | Min trades | Breadth |
|---|---|---|---|---|---|---|
| F1a FX_EU_SHORT | Breedon & Ranaldo (2013): a currency falls in its own trading hours; EURUSD only pair profitable after the EBS spread; sample ends 2007, no replication found | London 07:00 -> 13:00, short | EURUSD, GBPUSD | stop 0.5, 1.0 daily ATR | 300 | GBPUSD > 0 (1) |
| F1b FX_US_LONG | same paper: USD falls in US hours | London 13:00 -> 20:30, long | EURUSD, GBPUSD, AUDUSD, NZDUSD | stop 0.5, 1.0 | 300 | 2 of 3 |
| F2 INDEX_ROD_MOMENTUM | Baltussen, Da, Lammers & Martens (JFE 2021): return from the previous close to 15:30 predicts the last 30 minutes in 60+ futures (ES OOS R² 2.3 %); one blog finds it flat 2022-26 | New York 15:30 -> 16:00, `with_day` | US500, NAS100, US30 | stop 0.5, 0.25 | 300 | 1 of 2 |
| F2-EU (breadth legs of F2) | Baltussen et al. Table B1: rest-of-day slope Euro Stoxx 4.98, FTSE 4.28, DAX 3.42 (all t > 6, gross); added 2026-11-09 before any F2 result | London 16:00 -> 16:30 (UK100); Berlin 17:00 -> 17:30 (EU50, GER40), `with_day` | UK100; EU50, GER40 | stop 0.5 | 300 | reported with F2: F2 counts as broad if >= 2 of UK100, EU50, GER40 are > 0 |
| F3 FOMC_MORNING | Lucca & Moench (2015): +49 bp in the 24 h before FOMC statements 1994-2011; mostly gone after 2015 (Kurov et al.); falsification only, low power | New York 09:30 -> 13:45, long, `fomc` vs `all` | US500, NAS100 | filter fomc, all (stop 0.5) | 40 | 1 of 1 |
| F4 TOM_INTRADAY | Etula et al. (RFS 2020), McConnell & Xu (2008): turn of month +48 bp over T-3..T+3, close-to-close only, intraday share unknown | New York 09:30 -> 16:00, long, `turn_of_month` (T-1..T+3) vs `all` | US500, NAS100, US30 | filter turn_of_month, all (stop 0.5) | 100 | 1 of 2 |

ATR clock: FX `UTC` 00:00-23:59 (tolerance 30 min); indices `America/New_York` 09:30-16:00 (so
`with_day` compares with the previous 16:00 cash close). Grids: `research/grids/timed_hold_*.toml`.

**Not run (dead in the reports):** pre-holiday (Ko & Yang: S&P t = 0.93, 1983-2019), day-of-week,
generic macro-announcement-day long, pre-ECB drift, gold session pattern (no peer-reviewed
evidence), unconditional overnight drift (net Sharpe -0.5), the M15 candidates (all cost-infeasible
or duplicates of failed families: `2026-11-09_m15_candidate_triage.md`).

**Cost pre-check (I-52 style):** F1 about 3 bp per session gross vs 0.02 R cost at a 0.5-ATR stop
(about 0.07 R gross if the effect still exists); F2 about 2.7 bp per day gross vs 1.5 bp cost
(thin: about +0.06 R gross vs 0.04 R cost at 0.5 ATR); F3 about 20-35 bp per event in the
published sample, about 0-10 bp after 2015; F4 about 10 bp per day close-to-close. All
`COST_FEASIBLE_UNKNOWN_EDGE`; F2 is the one where costs could decide.

**Prediction that would falsify each:** net R per trade of the primary cell <= 0 or its bootstrap
lower bound <= 0 (F1, F2); filter-day mean not above the `all` baseline (F3, F4).

## Gates (fixed before the run)

Reported per cell on the development period only (`--dev-only`, before 2021-09-14); V2 reports,
the user decides. A family passes only if its **primary cell** passes all of:

1. **Net R > 0** at normal costs and with every cost component doubled (pattern of
   `tools/alternating_path_gates.py`).
2. **Halves:** net R > 0 in both UTC halves of the symbol's development period.
3. **Effect, not drift:** for a calendar filter, mean net R per trade on filter days minus mean
   net R per trade on the **other** days of the `all` baseline (same window, same direction; the
   filter's entry dates are removed from the baseline, so the samples are disjoint) > 0: circular
   block bootstrap of each series independently (blocks of 5 trades, 10,000 resamples, seed
   2026110), 2.5 % quantile of the difference > 0. For a time-of-day family, the gate is the
   bootstrap 2.5 % quantile of mean net R per trade > 0.
4. **Breadth:** the predicted sign holds (net R > 0) on at least the number of secondary symbols
   the family names.
5. **Best-date removal:** net R stays > 0 without the 5 best trade dates.
6. **Minimum trades:** the family's minimum (fewer = "not enough evidence", not a pass).
7. **Data integrity:** count trades with more than 5 consecutive missing M1 minutes in
   `(entry, exit]`, a missing exit candle, or any invalid present candle (the user, 2026-11-09).

Multiple testing: every cell of every family is counted in the trial log; the family count and the
cell count are reported with the result. A cell that is not the primary cell is a robustness
check, never a replacement for a failed primary cell. The raw one-sided p-value of mean net R per
trade is reported per cell next to a family-wise level of 0.05 / 5 hypotheses = 0.01.

Added after the skeptic review (2026-11-09, before any run; measurement only, no hypothesis or
window changed except F1a's start, see below):

- **F1 drift control:** F1a (short EURUSD) and F1b (long EURUSD) bet in opposite directions on the
  same pair, so a USD trend in 2015-2021 helps one and hurts the other. F1 (local-hours
  depreciation) counts as supported only if **both** legs pass on EURUSD. The pairs are all
  USD-correlated: breadth is not independent evidence.
- **Index long families (F3, F4):** a long index trade earns the 2015-2021 bull-market drift, so
  gates 1-2 are weak there; only gate 3 (the disjoint difference) speaks for the effect.
- **F2:** long and short trades are reported separately (`by_direction`), so an up-drift on the
  long side is visible.
- **Swap:** the number of trades with swap is reported (expected 0: every exit is before the
  17:00 New York rollover).
- **F1a start:** 07:00 London, the paper's European open (SNB WP 2011-04, Table 1: Europe 07:00-15:00
  London, sessions opening-to-opening); first drafted as 08:00, changed before any run. F1b ends at
  20:30 London instead of the paper's next European open: a day-trade adaptation, labelled so.
- **Data timing checked** (2016-2019, US-DST-but-not-EU weeks): US500 volatility peaks at 20:00
  UTC (16:00 EDT close) and both US500 and EURUSD peak at 18:00 UTC on the March FOMC days (14:00
  EDT), so the cached UTC timestamps are right in those weeks.
- **US30 dropped from F2 and F4** (before any F2 / F4 result): its cache starts 2019-02 and the
  runner's replay fails on years without candles. Breadth for both is NAS100 alone (1 of 1).
- **Diagnostics off** in the grids (`monkeys`, `sensitivity`, `entry_screen` = false): the matched
  monkeys took over 30 minutes per family; the gates above are the decision basis, the switches do
  not change what is tested.
- **Costs are lower bounds:** FX pairs other than GBPUSD and the indices before 2021 use today's
  FTMO spread scaled by price (the cost table report); gate 1 doubles every component.

## Hypothesis 6: F2L, momentum on large-move days (pre-registered 2026-11-09, after run 1)

Registered **after** the F2 results were seen, so it is a new hypothesis and counted as such
(6 hypotheses, 15 cells in total). The literature pass named it before any run (index momentum
report, rule 3): Gao et al. (2018) report stronger last-30-minute momentum on volatile days;
Baltussen et al. (2021) tie it to dealer gamma hedging, which scales with the size of the day's
move. F2 itself found the predicted sign gross in every index but about +0.01-0.03 R per trade,
below the 0.04-0.05 R cost; the hypothesis is that the edge per trade is larger on large-move days.

- Rule: F2 (`with_day`, last 30 minutes of the cash session, stop 0.5 daily ATR) plus
  ⚙️ `min_move_atr` = 0.5: trade only when |entry price - previous cash close| >= 0.5 daily ATR.
- Grids: `timed_hold_rodl.toml` (US500 primary, NAS100), `timed_hold_rodl_uk.toml` (UK100),
  `timed_hold_rodl_de.toml` (GER40; EU50 left out for its data gaps, decided before this run).
  One cell each; min trades 150; breadth: >= 2 of NAS100, UK100, GER40 net > 0.
- Gates: the same seven. Falsified if US500 mean net R per trade <= 0 or its bootstrap lower
  bound <= 0.

**Result (2026-11-09, development):** falsified. US500 675 trades, net -23.9 R (-0.035 R per
trade), gross +5.5 R (about +0.008 R per trade, smaller than on all days); NAS100 -13.0 net
(+4.6 gross), UK100 -23.9 (+13.4), GER40 +6.6 net (+17.5 gross, p 0.19, fails costs x2). Large-move
days do not lift the gross edge per trade above the cost. Folders
`results/research/timed_hold_rodl*_<hash>/gates.json`.

## Hypothesis 7: F1X, European-hours depreciation on crosses (pre-registered 2026-11-09)

Registered **after** the F1 results (counted as new; 7 hypotheses, 16 cells). F1a on EURUSD was
the only near-pass, and on EURUSD both legs were positive in opposite directions (+72.5 / +39.5 R),
which a trend cannot do. A sharper test of the mechanism (Breedon & Ranaldo: a currency falls in its
own trading hours) on pairs never run here: in 07:00-13:00 London, EUR and GBP are in their home
hours, JPY and AUD are not, so EUR and GBP should fall against them.

- Rule: F1a's (London 07:00 -> 13:00, short, stop 0.5 daily ATR, UTC daily ATR).
- Grid `timed_hold_fx_eu_x.toml`: EURJPY (primary), EURAUD, GBPJPY, GBPAUD; one cell.
- Gates: the same seven; breadth >= 2 of EURAUD, GBPJPY, GBPAUD net > 0. Falsified if EURJPY
  mean net R per trade <= 0 or its bootstrap lower bound <= 0. Gross R is reported too (crosses
  are expensive: GBPJPY about 0.065 R per trade at this stop).

**Result (2026-11-09, development):** falsified after costs, sign confirmed gross. Every cross
is gross positive in the predicted direction (EURJPY +41.6, EURAUD +34.0, GBPAUD +35.7, GBPJPY
+25.4 R over about 1,720 trades each, about +0.015-0.025 R per trade) and every one is net negative
(EURJPY -41.8, EURAUD -26.1, GBPAUD -32.3, GBPJPY -72.4 R): the crosses cost about 0.04-0.06 R per
trade. Reading: the European-hours depreciation looks real but small (about 0.02 R per trade gross
at this stop); only EURUSD, the cheapest pair, clears its costs.

## Hypothesis 9: F4M, turn of the month held close to close (pre-registered 2026-11-09)

Multi-day holds are in scope since 2026-11-09 (the user: "yes, but regard the fees"). F4 tested only
open-to-close; the published effect is close to close: Etula, Rinne, Suominen & Vaittinen (RFS 2020,
"Dash for cash"): abnormal +48 bp over the turn-of-month window T-3..T+3 and -37 bp over T-8..T-4,
20 of 23 countries (as quoted in `knowledge/research/reports/2026-11-09_calendar_effects.md`; the
paper's day indexing is not re-checked here, so the rule below is defined on its own terms); McConnell & Xu (2008) about 15 bp per day over the 4-day
window. Counted as a new hypothesis (9 hypotheses so far).

- **Rule (needs `hold_days` / `month_day`, brief `briefs/timed-hold-multiday.md`):** long at the close of
  the M1 candle closing at the cash close of the 4th-to-last trading day of the month; exit at the cash
  close of the 3rd trading day of the next month: the hold earns the returns of the last 3 and the first
  3 trading days of the month turn (6 trading days, about 8 nights). Stop 2 x daily ATR (primary) or 3 x (second cell); no target.
- **Markets:** US500 (primary), NAS100 (New York 16:00 close, NYSE trading days, NYSE short days not
  skipped for this family: the window is calendar-defined); breadth legs UK100 (London 16:30), JP225
  (Tokyo 15:00 close; Monday-Friday trading days, Japanese holidays not modelled: assumption),
  GER40 (Berlin 17:30; data to 2020-06) on Monday-Friday trading days.
- **Control (gate 3):** the same 6-trading-day hold entered at the cash close of the 8th trading day
  of the month (a mid-month window); gate = mean net R per trade of TOM minus control > 0, bootstrap 2.5 %
  quantile > 0 (disjoint by construction).
- **Fees:** every fee in the engine: overnight swap (today's FTMO rates applied to 2015-2021, so
  conservative), triple swap on the Friday night, spread, commission, slippage. Pre-check: about 9
  swap nights x 1.6-2.3 bp (US500 / NAS100) = 15-21 bp vs about 48 bp published gross: feasible.
- **Gates:** the seven gates; min trades 60 (12 a year x about 6.7 years); breadth: >= 2 of NAS100,
  UK100, GER40, JP225 net > 0. Falsified if US500 TOM minus control <= 0 or its bootstrap bound <= 0.

**Result (2026-11-09, development 2015-2021; `results/research/timed_hold_tom_multi*_<hash>/`):**
falsified on gate 3. TOM minus mid-month control, mean net R per trade (bootstrap 2.5 %): US500 stop 2:
+0.014 (-0.20), stop 3: +0.046 (-0.10); NAS100 -0.047 / -0.028; UK100 +0.142 (-0.09) / +0.097 (-0.07);
GER40 -0.004 / -0.071; JP225 -0.162 / -0.059. US500 TOM itself: 78 trades, gross +6.8 R, swap -14.9 R,
net -9.0 R (stop 2). The month turn is no better than a mid-month week in any market at a significant
level; the gate does not depend on the swap level (both windows pay about the same nights).
**Swap caveat:** the engine charges swap as a fixed money amount per lot at 2026 rates and prices; at
2015-2021 index levels that is about 3x too much in percent terms (US500 about 4-5 bp per night
instead of about 1.6), before the lower policy rates of those years. Multi-day results are therefore
conservative on financing until the user decides on scaling (HANDOFF › Open 9).
**Rerun with price-scaled swap** (the user's Open 9 (a), `df600b4`; `results/swapfix_2026-11-09/`):
US500 TOM stop 2 swap -5.0 R (was -14.9), net +0.9 R (gross +6.8, 78 trades); TOM minus control +0.012
(-0.21); NAS100 -0.067 (-0.29), UK100 +0.144 (-0.09), GER40 -0.008 (-0.27), JP225 -0.168 (-0.40).
Verdict unchanged: no turn-of-month effect beyond a mid-month week.

## Hypothesis 10: I-03 RSI(2) index mean reversion (pre-registered 2026-11-09)

Source: Kaufman, *Trading Systems and Methods* p.389-390 (knowledge card I-03): RSI(2) of daily closes,
long below 10 / short above 90, exit after one bar; S&P showed continuation before about 1998 and mean
reversion after, both sides working 2000-2008, cost-sensitive. Second cell family: the long-only
practitioner form with a 200-day trend filter (Connors; named as an optional filter on the card).
Label PUBLISHED (book, gross, pre-2009 sample); our 2015-2021 data is out of its sample. Counted as a
new hypothesis (10 so far). Multi-day hold allowed (fees counted).

- Signal on the daily cash session close (New York 16:00; RSI(2) of the regular-session closes, Wilder
  smoothing, known at that close); entry at that close, exit at the cash close `hold_days` later, stop
  2 x daily ATR. One position at a time per symbol.
- Cells (8): rule {K = both sides, RSI2 < 10 long / > 90 short; C = long only, RSI2 < 10 and close >
  200-day SMA of closes} x threshold {10/90, 5/95} x hold {1, 3 days}. **Primary: K, 10/90, hold 1**
  (Kaufman's rule exactly). Symbols US500 (primary), NAS100 (breadth).
- Gates: the seven, bootstrap of mean net R per trade > 0 (no calendar baseline); min trades 100;
  breadth NAS100 net > 0. Fee pre-check: one swap night about 1.6 bp + spread about 1.6 bp vs a
  next-day reversal of tens of bp in Kaufman's sample: feasible, unknown edge.

**Result (2026-11-09, development 2015-2021, price-scaled swap; `results/research/timed_hold_rsi2_b7a03afb`):**
falsified, no cell advances. Primary K 10/90 hold 1: US500 309 trades, net -3.9 R (gross +1.9; longs
+0.3, shorts -4.1), bootstrap -0.063, p 0.70; NAS100 -7.3. Long-only C cells: 31-69 trades, all within
+-2.3 R. Best non-primary cell K 5/95 hold 3: NAS100 +9.1 R (p 0.16), US500 +3.3 (p 0.35), first half
negative: a robustness cell, not a pass. Kaufman's post-1998 S&P reversal does not show net of fees in
2015-2021. 8 cells counted (10 hypotheses, 32 cells in total).

**Screened out, not built:** overnight index drift (close to open): about 1.5 bp per night gross
(Boyarchenko et al., NY Fed, as quoted in the calendar report) vs about 1.6 bp spread + 1-2 bp swap per
round trip: cost-infeasible. Currency carry on FTMO CFDs: both swap sides are negative for most pairs
(e.g. AUDUSD long -3.04 / short -6.54 per lot), so the carry is not harvestable here.

## Hypothesis 11: Gotobi USDJPY (pre-registered 2026-11-09, before any run)

Source: Bessho, Sugimoto, Suzuki, "Forex Trading Strategy That Might Be Executed Due to the Popularity
of Gotobi Anomaly", arXiv:2301.13204 (2023), OPENED (HTML): EBS USDJPY 2018-2020, Tuesday-Friday;
long from about 03:00 JST to the 09:55 JST Tokyo fix on gotobi days, net of spread "N=185, PF=1.46,
W=0.60" (no moving-average filter), non-gotobi days PF 0.52 with the MA filter; a second rule sells
09:55-12:00 JST. No gross bp per day given. Mechanism: Japanese importers buy USD at the 09:55
bank fixing on settlement days (5th, 10th, ... ; Ito and Yamada, JIE 2017, on the Tokyo fixing; the
gotobi magnitude of 4-9 bp in a Gemini scan is NOT verified). Label PUBLISHED (working paper, short
sample inside our development period, so not out of sample). Counted as hypothesis 11. Fee pre-check:
USDJPY round trip about 1.1 bp (spread + commission at 2015-21 prices) plus a long-swap credit for the
night crossed; daily ATR about 60 bp, so a 1-ATR stop costs about 0.02 R against an unknown gross edge.
Gemini's month-end-fix, OPEX and quarter-end items were already covered (calendar report) or need
cross-symbol signals; the gap fade is strategy 5; not re-tested here.

- **Gotobi day:** for each month the target dates 5, 10, 15, 20, 25 and the last calendar day; the
  gotobi day is the target date if it is a Tokyo business day, else the previous Tokyo business day
  (paper: "the previous business days were included if Gotobi days were holiday"). Tokyo business
  day = Monday-Friday, not a Japanese national holiday (`calendars/jp_holidays.csv`, Cabinet Office
  list) and not Dec 31, Jan 2 or Jan 3 (bank holidays). Two targets on the same day = one day.
- **G1 (primary family):** long USDJPY, entry at the close of the candle closing 03:00 Asia/Tokyo, exit
  at the close of the candle closing 09:55 Asia/Tokyo, same day; stop `stop_atr` x daily ATR (UTC days,
  as F1a). Monday entries fall on Sunday 18:00 UTC (market closed): no trade, which matches the paper's
  Tuesday-Friday sample. Cells: day_filter {gotobi, all} x stop_atr {1.0, 2.0}. **Primary: gotobi,
  stop 1.0, USDJPY.** Breadth: EURJPY (1 of 1; yen-side, not independent of USDJPY).
- **G2:** short USDJPY 09:55 -> 12:00 Asia/Tokyo on gotobi days (the paper's second rule without its
  pre-09:00 profit condition); same cells; primary gotobi, stop 1.0; breadth EURJPY.
- Gates: the seven above; gate 3 = gotobi minus the disjoint non-gotobi days of the `all` cell; min
  trades 200 (about 380 expected); family-wise level 0.05 / 11. G1 crosses the FTMO daily rollover
  (one swap night, triple on Wednesdays, counted): if gate 7 fails only through missing minutes in
  the rollover hour, the result is parked for the user, never passed.
- 16 runs (2 families x 4 cells x 2 symbols), 8 cells counted.

**Result (2026-11-09, development 2015-01-02..2021-09-13; `results/research/timed_hold_gotobi_d9ea62c1`,
gates `tools/timed_hold_gates.py --primary-symbol USDJPY --min-trades 200 --min-breadth 1`):**

- **G1 primary (gotobi, stop 1.0): passes gates 1-6, fails gate 7 (data integrity).** USDJPY 413
  trades, net +16.5 R (gross +23.2), +0.040 R per trade, every cost doubled +9.7 R, halves +9.7 / +6.9,
  without the 5 best dates +11.0 (doubled +4.2), bootstrap 2.5 % +0.013, p 0.0035 (below the
  family-wise 0.05 / 11 = 0.0045). Gate 3: gotobi minus the disjoint other days +0.078 R per trade,
  2.5 % bound +0.047 (the all-days cell is -62 R pooled, so the window itself loses). Breadth EURJPY
  +15.4 R (p 0.0016). Years USDJPY 2015-2021: +1.0, +4.1, +4.2, +4.9, -2.6, +1.6, +3.3 (EURJPY all seven
  positive); 2015-2017 lies before the paper's 2018-2020 sample. Stop 2.0: same gates, +17.9 R pooled.
- **Gate 7:** 9 USDJPY and 14 EURJPY trades have a gap of more than 5 M1 minutes; all exit candles
  present, no invalid candles. 21 of the 23 gaps fall in the FTMO daily rollover hour (21:00-23:00
  UTC, 6-60 minutes, Dec 24 the longest); 2 USDJPY trades have a 6-minute gap outside it
  (2020-12-29 18:41 UTC, 2021-06-03 20:21 UTC). So the pre-registered rule ("parked for the user,
  never passed" if only the rollover hour fails) does not strictly apply either: **G1 fails gate 7
  as registered**, parked for the user (HANDOFF › Open 10). Without the 23 trades: USDJPY +17.1 R
  (404 trades), EURJPY +16.4 R (399).
- **Gate 7 decision (rule set by the user, 2026-11-09, option a):** for holds that cross the FTMO
  daily rollover, M1 gaps inside the rollover hour (21:00-23:00 UTC) and gaps of up to 6 minutes
  elsewhere do not fail gate 7; a missing exit candle or an invalid candle still does. Under this
  rule G1 has 0 integrity failures and **passes all seven gates: ready for the one-time test**
  (Test=manual; criteria below).
- The timed-hold gate report applies this tolerance and also reports the strict integrity count.
- **One-time test criteria (pre-registered 2026-11-09, before any test data is seen; runs only on
  the user's go):** the primary cell exactly as run (`research/grids/timed_hold_gotobi.toml`, family
  G1, `day_filter = "gotobi"`, stop 1.0, USDJPY), nothing re-tuned, on 2021-09-14 to the last cached
  day. **Confirmed** only if all hold: (1) USDJPY net R > 0 at normal costs and with every cost
  doubled; (2) bootstrap 2.5 % quantile of mean net R per trade > 0 (gate scheme); (3) net R > 0 in
  both halves of the test period; (4) mean net R per trade >= half the development value (0.020 R).
  Anything else is "not confirmed", recorded either way. EURJPY reported alongside, not a gate.
- **G2 (short 09:55 -> 12:00): falsified** (gate 3, breadth and best-date removal fail).
- Gap listing (diagnostic, not a gate): `integrity_failures` per trade, gap start and length.


## Hypothesis 12: month-end post-fix USD rise (pre-registered 2026-11-09, before the confirmation run)

Origin: **found in the development data**, not taken from a paper (screen
`knowledge/research/reports/2026-11-09_fix_w_pattern_screen.md`, Codex, 84 window x symbol cells): on the
last weekday of the month the USD rises in 16:00-18:00 London after the WMR fix, EURUSD 5.5 bp (t 3.2),
GBPUSD 7.9 (3.6), AUDUSD 8.1 (3.4), NZDUSD 8.0 (3.6), 78 month-ends each, costs 0.8-1.8 bp. Mechanism
in print: equity-hedge rebalancing into the month-end fix that "partly reverts" afterwards (Melvin and
Prins, J. Financial Markets 22, 2015, abstract only); the USD falls after fixes on ordinary days (Krohn,
Mueller, Whelan, JF 79(1) 2024, Bank of Canada summary), so the month-end sign is the opposite of the
daily pattern. Because the development data found it, **development gates prove nothing**; the decision
rests on unseen 2010-2014 data. Counted as hypothesis 12 (the 84 screen cells are reported with it).

- Rule: short EURUSD, GBPUSD, AUDUSD, NZDUSD (USD long) at the close of the candle closing 16:00
  Europe/London on the last weekday of the month (`day_filter = "month_day"`, `month_day = -1`,
  `trading_days = "weekdays"`), exit at the candle closing 18:00 London; stop 1.0 x daily ATR (UTC days,
  as F1a). No swap (exit before the 17:00 New York rollover). Control cell: the same window on all days.
- Grid `research/grids/timed_hold_me_fix.toml`: day_filter {month_day, all} x stop {1.0}; 4 symbols.
- **Confirmation (decisive), 2010-01-01..2014-12-31** (data before the development split, outside
  the test period; MT5 cache from 2010, results in `results/presample_2010_2014/`): passes only if
  (1) pooled net R of the 4 pairs > 0 at normal costs and with every cost doubled; (2) at least 3 of 4
  pairs net R > 0; (3) pooled bootstrap 2.5 % quantile of mean net R per trade > 0 (gate scheme);
  (4) pooled net R > 0 in both halves (2010-2012, 2013-2014); (5) pooled month-end mean net R per trade
  minus the disjoint all-days mean > 0 (bootstrap 2.5 % > 0). About 240 trades.
- Development run reported alongside (descriptive). Pass -> parked "ready for the one-time test".
- **Amendment (2026-11-09, before any confirmation data was read):** the MT5 cache has no candles
  before 2015 (the 2010-2014 folders are empty), so the confirmation runs on the pre-sample histdata
  setup of F1a instead: **2008-01-01..2014-12-31**, `data/cache/histdata_presample/`, results in
  `results/presample_2008_2014/`; halves 2008-2011 / 2012-2014; per-year clock check as for F1a.
  EURUSD and GBPUSD are cached; AUDUSD and NZDUSD need a histdata download (the user's go,
  HANDOFF › Open 11). Criteria (1)-(5) unchanged over the 4 pairs; if the user declines the download,
  they apply to EURUSD + GBPUSD with criterion (2) = both pairs net R > 0. About 330 trades (4 pairs).
- **Development (descriptive, `results/research/timed_hold_me_fix_d686ffdd/`):** 312 pooled month-end
  trades, +18.7 R net, +13.5 R doubled costs, bootstrap 2.5 % +0.027 R; all seven tool gates pass
  (expected: the screen found it here). Report `knowledge/research/reports/2026-11-09_me_fix_h12.md`.

## Results, development run 1 (2026-11-09, `--dev-only`, 2015-01-02..2021-09-13)

Gates: `python -m backtester.tools.timed_hold_gates <folder> --primary-symbol ...` ->
`gates.json` in each `results/research/timed_hold_<family>_<hash>/`. Primary cells; R per trade
net of normal costs; "boot" = bootstrap 2.5 % quantile of mean net R per trade; p = raw one-sided.
Nothing is reported as profitable: no family advances. The user decides.

| Family | Primary | Trades | Net R | Gross R | Net R / trade | Halves | boot | p | Failed gates |
|---|---|---|---|---|---|---|---|---|---|
| F1a FX_EU_SHORT | EURUSD 0.5 | 1,723 | +72.5 | +112.9 | +0.042 | +56.4 / +16.0 | +0.007 | 0.008 | breadth (GBPUSD -25.8 net, +70.4 gross), data integrity (32 trades) |
| F1b FX_US_LONG | EURUSD 0.5 | 1,719 | +39.5 | +79.9 | +0.023 | +58.0 / -18.5 | -0.018 | 0.14 | costs x2, halves, boot, breadth (AUD, GBP, NZD negative), best dates, integrity |
| F2 ROD momentum US | US500 0.5 | 1,605 | -54.7 | +16.1 | -0.034 | -47.5 / -7.1 | -0.055 | 1.00 | all but min trades (NAS100 -21.3 net, +21.2 gross) |
| F2-EU UK | UK100 0.5 | 1,666 | -54.1 | +28.8 | -0.032 | -27.0 / -27.1 | -0.047 | 1.00 | all but min trades |
| F2-EU DE | EU50 0.5 | 882 | -34.8 | +10.2 | -0.039 | -30.0 / -4.7 | -0.062 | 1.00 | all; 556 of 882 trades touch a missing candle; GER40 +9.9 net (p 0.18) |
| F3 FOMC_MORNING | US500 fomc | 52 | -14.1 | -11.7 | -0.271 | -7.0 / -7.1 | diff -0.44 | 1.00 | all; filter minus other days -0.26 R / trade (NAS100 -0.32 R / trade) |
| F4 TOM_INTRADAY | US500 tom | 315 | -18.6 | -4.1 | -0.059 | -18.7 / 0.0 | diff -0.17 | 0.86 | all; filter minus other days -0.05 R / trade |

Reading (Opus):

- **F1 (local-hours depreciation) is not supported by the pre-registered rule** (both legs must
  pass on EURUSD; F1b fails). F1a alone on EURUSD is the strongest single result in V2 so far
  (net positive with every cost doubled, both halves, five best dates removed, p 0.008 < 0.01),
  but GBPUSD disagrees after costs (it agrees gross) and the second half is weaker. It was 1 of 12
  cells; it is a lead for the user's decision, not a pass.
- **F2:** the last-30-minute momentum has the predicted sign gross in every market (US500 +16,
  NAS100 +21, UK100 +29, GER40 +36, EU50 +10 R) but at about +0.01-0.03 R per trade it is far below
  the 0.04-0.05 R cost. Same finding as R014 and the M15 batches: a real but tiny gross edge.
- **F3 is falsified** in 2015-2021: FOMC mornings were worse than other mornings, the opposite of
  the published 1994-2011 drift (in line with the post-2015 decay reports).
- **F4:** no turn-of-month effect open to close.
- **Data:** many index trades touch a missing M1 candle (US500 in the `all` baseline: 808 of
  1,669; EU50 556 of 882; AUDUSD / NZDUSD about 25 % in F1b). Diagnosis (2026-11-09): the US500
  development data is histdata only (MT5 from 2021-09-15); the gaps are mostly omitted quiet
  minutes (about 10,000 one-minute gaps, only about 130 longer than 5 minutes; worst year 2017,
  median 23 missing minutes per cash day; NAS100 about 15 times fewer). They do not change a price
  path, so the strict gate (any missing minute) over-flags: with a 5-minute tolerance 78 of the 808
  US500 trades remain. 39 index trades of the `all` baselines carry swap: holiday / early-close days
  with no 16:00 candle, where `TimedExit` closes at the first later candle (18:01-18:03 ET).
  Neither changes a verdict above (every family fails other gates too). Open for the user: a
  gap-tolerant integrity gate and skipping NYSE closure / early-close days in index families.

## Run 1 follow-ups (2026-11-09)

- **FX ATR fix (code review by a sub-agent):** with UTC days 00:00-23:59 and tolerance 30, no
  Friday was regular (the FX data ends about 21:00 UTC) and the Sunday-evening stubs were, so the
  FX daily ATR was about 8 % too small and the FX stops too tight. Fixed as a measurement change:
  ⚙️ `atr_skip_weekend` (leave Saturday / Sunday ATR dates out) and tolerance 180 in the FX grids.
  Rerun: F1a EURUSD +68.9 R net (+0.040 R per trade, halves +50.1 / +18.9, bootstrap +0.008,
  p 0.0067), GBPUSD -25.6; F1b EURUSD +29.2 (second half -20.2); F1X all four net negative, gross
  positive. **No verdict changes.** Index families are not affected.
- **Placebo profile (diagnostic, not a selection; `timed_hold_placebo_eurusd.toml`):** EURUSD
  long, 6-hour holds from every London hour 00-17. Gross R long: 00-01 h +42 / +45, 04-11 h -30 to
  -86 (07 h the extreme: -86), 13-15 h +66 / +47 / +38, 17 h -33. A smooth daily shape that matches
  Breedon & Ranaldo (EUR weak in European hours, strong in US hours); the pre-registered 07:00 window
  (taken from the paper before any run) is its extreme. European weakness is negative in both
  halves for every 04-11 h start; the US-hours strength is positive in the first half only.
- **F1a dissection** (`knowledge/research/reports/2026-11-09_f1a_eurusd_dissection.md`): 6 of 7
  years positive, but 2020-21 together only +2.4 R vs +70 R in 2015-19; the top 1 % of trades
  (17) carry 58 % of the net; F1a and F1b daily R are uncorrelated (0.003), and the yearly drift
  does not explain F1a (correlation -0.10). A thin, fading lead.
- **Independent replication** (`knowledge/research/reports/2026-11-09_f1a_independent_replication.md`,
  plain M1 script, no engine): EURUSD short 07:00 -> 13:00 London close-to-close is +3.28 pips per
  day gross (t 4.34, 1,732 days), positive in every year but decaying (2015 5.6, 2016-18 about
  3.5, 2019 2.5, 2020 1.5, 2021 2.2 pips per day); GBPUSD +2.25 (t 1.96, uneven). The engine's
  trades match it exactly (entry / exit prices within 0.5 pip on 100 % of time exits, per-day
  correlation 1.000). Our EURUSD round trip costs about 0.9 pip. The hourly shape: European hours
  negative in both 2015-17 and 2018-21; the US-hours positive half only in 2015-17.
- **Gates tool:** variants of a grid with `[[grids]]` families are now keyed by family too (the
  hypothesis grids each had one family; only the placebo grid needed it).

## F1a one-time test criteria (pre-registered 2026-11-09; the test runs only on the user's go)

If the user approves the one-time MT5 test (2021-09-14 to the last cached day) of F1a, it runs the
primary cell exactly as rerun after the ATR fix (`research/grids/timed_hold_fx_eu.toml`, EURUSD,
stop 0.5, `atr_skip_weekend`, tolerance 180), nothing re-tuned. F1a counts as **confirmed** only if
all hold on the test period: (1) EURUSD net R > 0 at normal costs and with every cost doubled;
(2) mean net R per trade bootstrap 2.5 % quantile > 0 (same scheme as the gates); (3) net R > 0 in
both halves of the test period; (4) mean net R per trade >= half the development value (0.020 R).
Anything else is "not confirmed", and the result is recorded either way. GBPUSD is reported with it,
not as a gate (it failed breadth on development).

## F1a pre-sample check 2008-2014 (pre-registered 2026-11-09; the user's go the same day)

Untouched EURUSD / GBPUSD histdata 2008-2014 in a separate raw root and cache
(`data/raw/histdata_presample/`, `data/cache/histdata_presample/`), results in
`results/presample_2008_2014/` (own trial log); the main cache, the development / test split and
the test period are not touched. Same grid as the F1a rerun (`timed_hold_fx_eu.toml`, after the
ATR fix), nothing re-tuned. Before the run: a per-year histdata clock check of those years
(`results/clock_check_histdata_pre2015.md`); a year whose clock cannot be confirmed is excluded and
named. **F1a passes the pre-sample check** only if, on EURUSD stop 0.5: (1) net R > 0 at normal and
at all-doubled costs; (2) net R > 0 in both 2008-2011 and 2012-2014; (3) bootstrap 2.5 % quantile of
mean net R per trade > 0. Costs there are optimistic (2008-2014 uses the nearest measured spreads),
so (1) with doubled costs is the main cost check. GBPUSD is reported, not gated. Either outcome is
recorded; a pass is still not a strategy pass (the MT5 test needs the user's go).

**Result (2026-11-09):** histdata clock fixed first (US rule through 2018, verified on release
times: `knowledge/research/reports/2026-11-09_clock_check_pre2015.md`), pre-sample re-imported and
re-checked. `results/presample_2008_2014/research/timed_hold_fx_eu_6d5397f8/gates.json`. EURUSD stop
0.5: 1,789 trades, net **+40.4 R** (+0.023 R per trade, gross +69.9), all costs doubled +10.8,
2008-2011 +6.2 / 2012-2014 +34.2, bootstrap 2.5 % quantile **-0.009**, p 0.09; by year +7.0, -1.6,
+6.3, -5.5, +10.9, +7.4, +15.8. Criteria (1) and (2) hold, **(3) fails: F1a does not pass the
pre-sample check.** The sign holds over all 14 years 2008-2021 (2008-14 +40 R, 2015-21 +69 R),
at about half the development size before 2015. GBPUSD -0.9 net (+59.4 gross). 589 EURUSD trades touch
a missing minute (older histdata is sparser; strict rule). Reading: a small, persistent EURUSD
European-hours drift that is about at the edge of our costs, not a robust edge.

Gap-tolerant integrity gate (the user, 2026-11-09; > 5 consecutive missing minutes or a missing exit
candle): F1a EURUSD failures drop from 33 to 6 (development, ATR-fixed run) and from 589 to 3
(pre-sample); the verdicts do not change (breadth, and the pre-sample bootstrap, still fail).

## Backtest options

- Costs as the engine default (fixed spread; spread table off by default). Swap: none for a day
  trade unless an exit falls after the 17:00 New York rollover.
- Research runner, development only: `python -m backtester.tools.research
  research/grids/timed_hold_<family>.toml --dev-only`.

## Assumptions (decided by Opus, 2026-11-09)

- FX daily ATR on UTC dates (not the 17:00 New York trading day): simpler, and the stop only needs
  the scale of a day's range, not its exact boundary.
- An entry candle that is missing means no trade (no fallback to a later candle): an entry price
  from a different time would test a different window.
- Calendar dates are taken as published; the FOMC statement time is not used by the rule (entry and
  exit are clock times of the family).
