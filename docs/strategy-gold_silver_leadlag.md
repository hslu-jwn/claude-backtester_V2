# Strategy 15: Gold impulse -> silver delayed continuation (cross-metal lead-lag)

Spec drafted 2026-11-10; pre-build screen 2026-11-12 failed (ledger, research log): not built, stays a card. Planned folder
`strategy/gold_silver_leadlag/`, config `GoldSilverLeadlagConfig`, registry name `gold_silver_leadlag`.
Reads a **reference symbol** (XAUUSD) while trading another (XAGUSD): `docs/design/multi-symbol.md` > A
(opt-in `on_market_candle`, one execution symbol, reference data only through a snapshot bounded by the
current engine time). Cannot run before multi-symbol step 1a.
Grid: `research/grids/gold_silver_leadlag.toml` (marked do not run before integration).

## Source and prior

World Gold Council, "Gold safe haven versus silver wildcard" (opened abstract/publication page;
`knowledge/research/reports/2026-11-10_idea_harvest_multisymbol.md`, idea 11): reports one-minute
gold-to-silver Granger causality / price discovery significance, not trading P/L. The publication
pools data through 2026, overlapping the protected test era; no use of its sample as an independent
holdout. Label PRACTITIONER.

Mechanism: Silver may react more slowly to macro, monetary, and safe-haven flow shocks first priced
in gold, the much larger, deeper, and more liquid market.
Prior: Silver is more volatile than gold (gold-to-silver beta > 1), but short-horizon lead-lag effects
may be largely absorbed intraminute or within seconds by algorithmic market makers. A 2-hour holding
period faces notable bid-ask spread and slippage relative to the net move: absolute 2-hour silver move
is typically 20-150 bp against 5-20 bp round-trip cost and potentially elevated event spreads.
Gross signed edge is unproven, and one-minute statistical Granger causality does not imply an hourly
delayed tradable effect after costs. Counted as a new hypothesis, 8 cells, in the trial log.

## Rule and definitions

Base timeframe **1m**. Higher timeframe clock: **H1** (signal evaluation) and **D1** (Wilder ATR stop).
All clock times are in **UTC**.

- **Active signal window:** H1 candle closes occurring during **12:00–19:00 UTC** (London afternoon and
  New York morning liquid overlap; H1 closes at 12:00, 13:00, 14:00, 15:00, 16:00, 17:00, 18:00, 19:00 UTC).
- **Signal calculation:** At each qualifying H1 close `t`, calculate the XAUUSD one-hour log return:
  `r = 100 * ln(C_t / C_{t-1})` in percent, where `C_t` is the close of the XAUUSD candle closing at `t`
  and `C_{t-1}` is the close of the candle closing 60 minutes earlier (`t - 1h`). Both candles must exist;
  if either is missing, no signal and no trade (no fallback). Reference data are read only through the
  bounded snapshot up to `now`; nothing after `now` is visible.
- **Entry:** Direction **long** if `r >= +threshold`, **short** if `r <= -threshold`, otherwise flat (no trade).
  Entry occurs at the close of the matching XAGUSD M1 candle closing at the H1 mark (e.g. 12:00:00 UTC).
  Fills at close / open of next candle per engine rules. Both XAUUSD and XAGUSD H1 candles must have closed.
- **Exit:** Timed exit after `hold_minutes` (120 or 180 minutes: candle closing at `entry_time + hold_minutes`),
  or when the stop loss is hit.
- **Stop:** `stop_atr` x XAGUSD daily ATR(14) from entry price, placed against the trade direction, no target.
  If SL is touched within a candle: engine rules apply (SL hit first).
- **Daily ATR:** Wilder ATR(14) of XAGUSD daily sessions, using only completed daily sessions finished
  before the entry candle closes. No trade until 14 sessions exist.
- **Position concurrency:** Exactly **one position at a time** (no overlapping trades). If a position is
  currently open in XAGUSD, any subsequent H1 signal is ignored until the position has completely exited.

## Calendars and session clocks

- Precious metals trade on CME Globex / OTC market hours: Sunday 23:00 UTC to Friday 22:00 UTC, with a
  daily 1-hour maintenance break (17:00–18:00 America/New_York, which corresponds to 21:00–22:00 UTC in
  US summer time and 22:00–23:00 UTC in US winter time).
- The active evaluation window 12:00–19:00 UTC and holds up to 180 minutes ensure that trades entered at or
  before 19:00 UTC exit by 22:00 UTC, completely avoiding the daily maintenance break and avoiding overnight
  rollover swap at 17:00 New York.
- CME / US bank holidays (Christmas, New Year, Thanksgiving, etc.) with early closes or closures are
  handled conservatively: if any required M1 candle for the H1 reference return or the entry bar is
  missing, no trade is taken.

## Cells (pre-registered, 8)

Threshold {0.40 %, 0.50 %} x stop {1.0, 1.5} daily ATR x hold {120 min, 180 min} = 8 cells.
**Primary cell: 0.50 % / 1.0 ATR / 120 min** (the harvest report idea 11 rule exactly).
The other 7 cells are pre-registered robustness checks, never replacements for a failed primary.
Traded symbol: XAGUSD; reference symbol: XAUUSD.

## Control

The same XAGUSD entry window and holding durations (entry at H1 closes 12:00–19:00 UTC, same exit time
and stop) on **all eligible trading days**, direction fixed, never a coin flip: an all-days **long** and
an all-days **short** baseline (grid family C).
For Gate 3, the dates and timestamps of the signal cell's trades are removed from both baselines
(disjoint samples). Each signal trade is compared with the baseline of its own direction on the remaining
instances, weighted by the signal trade mix (`n_long`, `n_short`):
`control_mean = (n_long * mean_long_baseline + n_short * mean_short_baseline) / (n_long + n_short)`.
Reason: a long signal in a rising precious metals market must beat plain "long at 12:00 UTC", so market drift
cannot masquerade as signal edge.

## Gates (fixed before any run)

Development period only (`--dev-only`; XAGUSD and XAUUSD histdata development window **2015-01-02..2021-09-13**).
Reported per cell; the user decides. The family passes only if its **primary cell** passes all seven
timed_hold-style gates (`tools/timed_hold_gates.py`):

1. **Net R > 0** at normal costs and with every cost component doubled (spread, slippage, commission, swap).
2. **Halves:** net R > 0 in both halves of the development period (split at 2018-05-08, the midpoint of the
   development trade dates).
3. **Effect, not drift:** mean net R per trade of the signal cell minus the matched control mean (see Control),
   circular block bootstrap of each series independently (blocks of 5 trades, 10,000 resamples, seed 2026110),
   2.5 % quantile of the difference > 0.
4. **Breadth:** Symmetric lead-lag test (XAGUSD impulse -> XAUUSD delayed continuation, same 0.50 % / 1.0 ATR /
   120 min rule): net R > 0. If the symmetric mechanism fails, report whether the effect is strictly unidirectional
   or absent.
5. **Best-date removal:** net R stays > 0 without the 5 best trade dates.
6. **Minimum trades:** 200 on the primary cell (fewer = "not enough evidence", not a pass). Pre-estimate:
   gold H1 moves >= 0.50 % during 12:00–19:00 UTC occur roughly 30–60 times per year x 6.7 years = 200–400 trades;
   cells with higher thresholds falling below 200 report "not enough evidence" and never gate.
7. **Data integrity:** count trades with more than 5 consecutive missing M1 minutes in `(entry, exit]` on
   XAGUSD, a missing exit candle, or an invalid present candle. Also counted and reported: signal evaluation
   hours where a XAUUSD signal candle is missing.

Multiple testing: the 8 cells are counted in the trial log (hypothesis 15 overall); raw one-sided p of
mean net R per trade reported per cell next to family-wise level 0.05 / 5 hypotheses = 0.01.
Falsified if the primary mean net R per trade <= 0, or its bootstrap 2.5 % lower bound <= 0, or Gate 3 fails.
Costs: XAGUSD histdata uses FTMO spread scaled by price (spread 0.049, slippage 0.0245, commission 0.000007 per side).
Gate 1 doubles every component. Long and short trades reported separately (`by_direction`).
Nothing is reported as profitable before the gates. One-time test (2021-09-14 onward, MT5): only on the
user's explicit go.

## Data facts (checked 2026-11-10)

- XAUUSD histdata cache: `data/cache/histdata/XAUUSD/` contains annual directories `2015` through `2026`.
- XAGUSD histdata cache: `data/cache/histdata/XAGUSD/` contains annual directories `2015` through `2021`
  (last file `2021-12-31.parquet`).
- Development period: `2015-01-02` to `2021-09-13` (per `AGENTS.md` rule: develop before 2021-09-14).
- Neither XAUUSD nor XAGUSD is listed in `INVALID_PERIODS` in `src/backtester/data/histdata.py`.
- MT5 cache: `data/cache/mt5/XAUUSD` and `data/cache/mt5/XAGUSD` exist from `2010` through `2026`
  (reserved for the one-time test from 2021-09-14 onward).
- Costs for XAGUSD in `src/backtester/engine/costs.py`:
  - `spread = 0.049`
  - `contract_size = 5000`
  - `slippage = 0.0245`
  - `commission_pct_per_side = 0.000007` (FTMO_METAL_COMMISSION_PCT_SIDE, i.e. 0.0014 % round turn)
  - `swap_long_per_lot = -68.05`, `swap_short_per_lot = 0.30`
  - `reference_price = 64.58` (REFERENCE_PRICES), `tick_size = 0.001`.

## Assumptions (conservative choices)

1. **Entry timing:** Entry executes at the close of the XAGUSD M1 candle closing at the H1 mark
   (e.g. 12:00:00 UTC), fills at close / open of next candle per engine rules.
2. **Snapshot isolation:** Reference data from XAUUSD are read strictly through the bounded market
   snapshot at or before `now`; no future prices or intraminute prices are visible.
3. **Signal return:** Log return `100 * ln(C_t / C_{t-1})` on completed H1 candles. Equality at the
   threshold (`>=` and `<=`) triggers entry.
4. **Missing candles:** If either boundary candle of the H1 window on XAUUSD or the entry candle on XAGUSD
   is missing, no signal is emitted and no trade occurs.
5. **No trade overlap:** Only one position in XAGUSD is open at any time. Any subsequent signal occurring
   while a trade is active is ignored.
6. **No overnight swap:** Since entries occur 12:00–19:00 UTC and max hold is 180 minutes, positions close
   at or before 22:00 UTC, before the CME daily maintenance break and before 17:00 New York rollover.
   Trades with swap are expected to be 0 and reported.
7. **Daily ATR:** Wilder ATR(14) uses completed daily sessions finished before the trade entry candle closes.
8. **Gate 2 split date:** 2018-05-08 is fixed from the development period midpoint, not from data.
9. **Config keys:** Proposed names (`ref_symbol`, `ref_timeframe`, `active_from`, `active_to`,
   `min_ref_return_pct`, `hold_minutes`, `direction = "with_ref"`).
10. **Costs:** Standard engine defaults; Gate 1 doubles all components.

## Decisions by Opus

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
- S15 ATR on New York days (G1); trades may cross the rollover and pay swap (G3). Breadth = the mirror run in its own grid (`gold_silver_leadlag_rev.toml`: XAUUSD traded, XAGUSD reference), same cells.
