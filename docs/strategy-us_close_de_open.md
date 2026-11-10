# Strategy 14: US close -> German open (cross-market overnight momentum)

Spec drafted 2026-11-10 (docs only, nothing built, nothing run). Planned folder
`strategy/us_close_de_open/`, config `UsCloseDeOpenConfig`, registry name `us_close_de_open`.
First strategy that reads a **reference symbol** (US500) while trading another (GER40):
`docs/design/multi-symbol.md` > A (opt-in `on_market_candle`, one execution symbol, reference data
only through a snapshot bounded by the current engine time). Cannot run before multi-symbol step 1a.
Grid: `research/grids/us_close_de_open.toml` (marked do not run before integration).

## Source and prior

Xu et al., "Cross-market overnight time-series momentum" (ResearchGate 398174368): the final half
hour of the US session predicts the first half hour of international markets the next trading day,
positive profit after assumed costs. Only the abstract page was opened
(`knowledge/research/reports/2026-11-10_idea_harvest_multisymbol.md`, idea 10); the full text was
not accessible, so instruments, timing, costs and fills here are **ours, not a replication**.
Label PUBLISHED (abstract only). Mechanism: US information diffuses into German cash-open order flow.
Prior: 30-minute absolute GER40 move at the open about 10-50 bp against a round trip of about 2-6 bp;
the conditional edge may be a fraction of the move, and the first open may already price the US news.
Distinct from the rejected same-index last-half-hour hold (F2, `strategy-timed-hold.md`). Counted as a
new hypothesis, 8 cells, in the trial log.

## Definitions

Base timeframe **1m**. All clock times are local in the named zone (DST via `zoneinfo`; the US and
German clocks shift on different weeks, so the Berlin clock time of the US close varies; only the
local clock times below are used).

- **Signal day** `D_s`: the weekday immediately before the trade day `D_t` (Monday uses Friday).
  `D_s` must be a full NYSE session (`strategy/timed_hold/calendars/nyse_holidays.csv`: not closed,
  not a 13:00 early close). If `D_s` is not a full session, no trade on `D_t`.
- **Signal** `r` = `100 * (C16 / C1530 - 1)` in percent, `C16` = close of the US500 M1 candle that
  closes at 16:00 America/New_York on `D_s`, `C1530` = close of the candle that closes at 15:30 that
  day. The first candle of the window is the one **closing at 15:31**; the 15:30 price is the close
  of the candle closing at 15:30. If either candle is missing, no trade (no fallback to a neighbour).
  Reference data are read only through the bounded snapshot; nothing after `now` is visible.
- **Trade day** `D_t`: a Monday-Friday that is a full NYSE session (also a normal day in the US) and
  on which GER40 has a candle closing at 09:00 Europe/Berlin. Missing 09:00 GER40 candle = closed or
  broken day, no trade (conservative German-holiday rule, see Assumptions).
- **Entry:** direction long if `r >= +threshold`, short if `r <= -threshold`, otherwise no trade. Entry
  at the close of the GER40 candle closing at 09:00 Berlin on `D_t`. The overnight gap (US close to
  09:00) is never part of the traded return: the trade starts at the 09:00 close.
- **Exit:** the close of the candle closing at `exit_time` (09:30 or 10:00 Berlin) on `D_t`, or the
  first later candle if it is missing, as `timed_hold` `TimedExit`.
- **Stop:** `stop_atr` x GER40 daily ATR(14) from entry, against the direction, no target. SL inside
  a candle: engine rules (SL first).
- **Daily ATR:** Wilder ATR(14) of the Berlin cash sessions 09:00-17:30 (regular = last candle within
  `atr_close_tolerance_min` of 17:30), `SessionStats`, using only sessions finished before the entry
  candle closes. No trade until it exists.
- One trade per day at most; a day-trade only, no swap (exit before 17:00 New York, expected 0 swap
  trades; reported).

## Cells (pre-registered, 8)

Threshold {0.10 %, 0.20 %} x stop {0.5, 1.0} daily ATR x exit {09:30, 10:00} Berlin = 8 cells.
**Primary: 0.10 % / 0.5 ATR / 09:30** (the harvest-report rule exactly). The other 7 are robustness
checks, never replacements for a failed primary. Symbols: GER40 primary; UK100 breadth.

## Control

The same GER40 window (09:00 entry, same exit and stop) on **all days**, direction fixed, never a coin
flip: an all-days **long** and an all-days **short** baseline (grid family C). For gate 3 the dates of
the signal cell's trades are removed from both baselines (disjoint samples). Each signal trade is
compared with the baseline of its own direction on the remaining days, weighted by the signal trade
mix (n_long, n_short): control mean = (n_long * mean_long_baseline + n_short * mean_short_baseline) /
(n_long + n_short). Reason: a long signal in a rising market must beat plain "long at 09:00", so
the drift of the sample cannot count as signal.

## Gates (fixed before any run)

Development only (`--dev-only`; GER40 data end 2020-06-14 by rule, so **2015-01-02..2020-06-14**; UK100
2015-01-02..2021-09-13). Reported per cell; the user decides. The family passes only if its **primary
cell** passes all (the `timed_hold` gates pattern, `tools/timed_hold_gates.py`):

1. **Net R > 0** at normal costs and with every cost component doubled.
2. **Halves:** net R > 0 in both halves of the GER40 development period (split at 2017-10-08, the
   midpoint of the trade dates).
3. **Effect, not drift:** mean net R per trade of the signal cell minus the matched control mean (see
   Control), circular block bootstrap of each series independently (blocks of 5 trades, 10,000
   resamples, seed 2026110), 2.5 % quantile of the difference > 0.
4. **Breadth:** UK100 at 08:00 London (exit 08:30 London, same 0.10 % / 0.5 ATR cell, same US500 signal
   on the same previous weekday; London ATR 08:00-16:30 London): net R > 0 (1 of 1). UK100 and GER40
   are both European index opens reacting to the same US news, so breadth is not independent evidence.
5. **Best-date removal:** net R stays > 0 without the 5 best trade dates.
6. **Minimum trades:** 200 on the primary cell (fewer = "not enough evidence", not a pass). Pre-estimate
   for 0.10 %: 60-130 per year x 5.4 years = 320-700; at 0.20 % fewer, possibly below 200: those
   cells then report "not enough evidence" and never gate.
7. **Data integrity:** count trades with more than 5 consecutive missing M1 minutes in `(entry, exit]`
   on GER40, a missing exit candle, or an invalid present candle (rule of the user, 2026-11-09).
   Also counted: signal days where a US500 signal candle is missing (reported, not a gate).

Multiple testing: the 8 cells are counted in the trial log (hypothesis 14 overall); raw one-sided p of
mean net R per trade reported per cell next to the family-wise level 0.05 / 5 hypotheses = 0.01 (as
`timed_hold`). Falsified if the primary mean net R per trade <= 0, or its bootstrap 2.5 % lower bound
<= 0, or gate 3 fails. Costs: GER40 histdata years use today's FTMO spread scaled by price (lower
bound), gate 1 doubles every component. Long and short trades reported separately (`by_direction`).
Nothing is reported as profitable before the gates. One-time test (2021-09-14 onward, MT5): only on the
user's go, criteria to be fixed then; GER40 and UK100 MT5 candles exist from 2021-09.

## Data facts (checked 2026-11-10)

- GER40 histdata cache: `data/cache/histdata/GER40/2015..2021`; the last file is 2020-06-14
  (`INVALID_PERIODS` in `src/backtester/data/histdata.py` drops GER40 from 2020-06-15, "GRXEUR files
  switch instrument"). Development period = 2015-01..2020-06. 2021 histdata GER40 dir exists but holds no
  valid rows after the cut; MT5 GER40 candles start 2021-09 (test era).
- US500 histdata `2015..2021`, then MT5 `2021..2026`. UK100 histdata `2015..2021`.
- NYSE calendar: `strategy/timed_hold/calendars/nyse_holidays.csv` (closed and early_close_13:00,
  2008-2026). No German or UK holiday calendar exists in the repo.

## Assumptions (conservative choices)

1. **German/UK holidays:** a missing 09:00 GER40 (08:00 UK100) candle means closed day, no trade. No
   external calendar is added; if one is wanted later, Deutsche Boerse trading calendar (Xetra).
   Half days (Dec 24 and 31 close at 14:00 Berlin) have the 09:00 candle and are traded: the
   09:00-09:30 window is normal, and the 17:30 ATR session is simply irregular that day.
2. **"Next day":** the weekday after `D_s`, and Monday uses Friday (a weekend gap before the trade is
   allowed since the gap is never traded). Days after a NYSE holiday do not trade (D_s not a full session);
   NYSE-open but German-holiday days are skipped by Assumption 1.
3. **Signal** is the plain M1 close-to-close return 15:30 -> 16:00 New York, not a log return and not
   the open of the first candle. `>=` / `<=` at the threshold (equality trades).
4. **No trade on a missing signal candle** (either end) and none on a missing entry candle.
5. **Direction conflict with the DST mismatch weeks** (US-DST but not EU-DST, about 3 weeks a year) is
   ignored: all times are local clocks, so the gap between the US close and the Berlin open changes
   (e.g. 1 h shorter); these days are reported as a diagnostic split, not removed.
6. **ATR:** same Berlin cash session definition as `strategy-timed-hold.md` F2-EU; the daily ATR needs
   14 finished sessions.
7. **Gate-2 split date** 2017-10-08 is fixed now from the period midpoint, not from data.
8. **Config keys** in the grid (`ref_symbol`, `ref_zone`, `ref_from`, `ref_to`, `ref_day_offset`,
   `min_ref_return_pct`, `direction = "with_ref"`) are proposed names, not implemented.
9. **UK100 breadth** uses London 08:00 -> 08:30 with the same threshold and stop; its London clock and the
   New York clock keep the 5-hour gap except in DST mismatch weeks.
10. **Costs** are the engine defaults (fixed spread, no spread table); no defaults changed.

## Decisions by Opus (2026-11-10, on the drafting agent's open questions, before any code or run)

1. Monday trades use the previous Friday's US signal (the weekend gap is never traded): yes.
2. German holidays: a missing GER40 09:00 Berlin candle means a closed day (no trade); no separate Xetra
   calendar. Short sessions (e.g. Dec 24 / 31 when open) trade if the candles exist.
3. US/EU DST-mismatch weeks (about 3 per year) are kept and reported as a separate split, not excluded.
4. The weighted control (signal-day long / short mix) and the UK100 per-symbol overrides are part of the
   gates; the gates tool must implement them before the run (integration work).
5. Cells at the 0.20 % threshold may end below 200 trades: reported as "not enough evidence", as written.

**Decided by Opus 2026-11-10, before any build or run:**

Global (all five lead-lag specs, after the skeptic review `knowledge/research/reports/2026-11-10_leadlag_skeptic.md`):
- G1 Daily bars / ATR: FX, metals, oil = 17:00 New York trading days, weekend stubs excluded (as timed_hold's
  `atr_skip_weekend`); crypto = UTC days with the Saturday-closure rule of `docs/research-runner.md`.
- G2 Execution: entries and timed exits fill at the close of the named candle (the engine's close-price
  entry, costs and slippage as usual), like every timed strategy; "the HH:MM candle" = the candle CLOSING at
  HH:MM (timestamps are opens).
- G3 A trade that crosses the FTMO daily rollover is allowed and pays the modelled swap (triple day included).
- G4 Minimum trades not reached = "not enough evidence", never "falsified" and never a pass.
- G5 A missing reference or entry candle = no trade that day (no fallback, no partial universe).
- S14 UK100 breadth runs as its own grid file `research/grids/us_close_de_open_uk.toml` (UK100 traded, entry 08:00 London close, exits 08:30 / 09:00), same cells.
