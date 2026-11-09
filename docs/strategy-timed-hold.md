# Strategy 10: Timed hold (published time-of-day and calendar effects)

Research run 1 of `Continue.Research` (2026-11-09). Folder `strategy/timed_hold/`, config
`TimedHoldConfig`, registry name `timed_hold`. Day trade: enter at a fixed clock time, hold in a
fixed direction, leave at a fixed clock time the same day; a wide stop in daily ATR.

Why this shape: our own cost table (`knowledge/research/reports/2026-11-09_cost_in_R_table.md`)
shows a round trip costs about 0.2 R at a 1-ATR M15 stop but only 0.02-0.04 R at a stop of half a
daily ATR. Every intraday signal we built (strategies 1-9, R014) had a gross edge of a few
hundredths of an R at M15 stops. Published effects of a few basis points per session can only pay
their costs with session-sized stops. This strategy is one engine for several **pre-registered
hypothesis families** (section Families); each family names its source, its prediction and its
gates before any run. It does not search for windows: entry and exit times come from the papers.

## Definitions

Base timeframe **1m**. Times are local clock times in ⚙️ `zone` (DST via `zoneinfo`).

- **Entry candle:** the 1m candle that **closes** at ⚙️ `entry_time` on a qualifying day. Entry at
  its close (known at that time, no lookahead). If that candle is missing, no trade that day.
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
  - `pre_holiday`: the last trading day before a full NYSE closure that falls on a weekday.
  The calendars are published in advance (scheduled meetings, exchange holiday rules), so using
  them at the entry time is not lookahead. Unscheduled FOMC actions are excluded.

## Rule

- **Direction:** ⚙️ `direction` = `long` or `short` (one code path by `Direction`), or
  `with_day` / `against_day`: long when the entry candle's close is above the close of the last
  finished regular ATR session (short when below, no trade when equal or unknown); `against_day`
  the opposite.
- **Stop:** entry ∓ ⚙️ `stop_atr` × daily ATR (long: below). No take profit.
- **Time exit:** a trade still open at ⚙️ `exit_time` closes at the close of the candle closing at
  that time, or at the first later candle if it is missing (`session_stats.TimedExit`).
  `exit_time` must be after `entry_time` on the same local date.
- One trade per day at most. SL inside a candle: engine rules (SL first).

## Families (pre-registered 2026-11-09, before any run)

From the literature reports in `knowledge/research/reports/2026-11-09_*.md` (sources marked opened
in full / abstract only there). Every number below is the papers', gross, on their samples; none
is ours. 4 families, 5 hypotheses, 10 grid cells. Primary cell = the first stop value listed.

| Family | Source and prior | Rule (zone, entry -> exit, direction) | Symbols (primary first) | Cells | Min trades | Breadth |
|---|---|---|---|---|---|---|
| F1a FX_EU_SHORT | Breedon & Ranaldo (2013): a currency falls in its own trading hours; EURUSD only pair profitable after the EBS spread; sample ends 2007, no replication found | London 07:00 -> 13:00, short | EURUSD, GBPUSD | stop 0.5, 1.0 daily ATR | 300 | GBPUSD > 0 (1) |
| F1b FX_US_LONG | same paper: USD falls in US hours | London 13:00 -> 20:30, long | EURUSD, GBPUSD, AUDUSD, NZDUSD | stop 0.5, 1.0 | 300 | 2 of 3 |
| F2 INDEX_ROD_MOMENTUM | Baltussen, Da, Lammers & Martens (JFE 2021): return from the previous close to 15:30 predicts the last 30 minutes in 60+ futures (ES OOS R² 2.3 %); one blog finds it flat 2022-26 | New York 15:30 -> 16:00, `with_day` | US500, NAS100, US30 | stop 0.5, 0.25 | 300 | 1 of 2 |
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
7. **Data integrity:** count of trades with a missing or invalid M1 candle inside the hold.

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
- **Costs are lower bounds:** FX pairs other than GBPUSD and the indices before 2021 use today's
  FTMO spread scaled by price (the cost table report); gate 1 doubles every component.

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
