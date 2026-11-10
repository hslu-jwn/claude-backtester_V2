# Strategy 18: Dollar breadth -> USDCAD (cross-market USD breadth)

Spec drafted 2026-11-10 (docs only, nothing built, nothing run). Planned folder
`strategy/usd_breadth_usdcad/`, config `UsdBreadthUsdcadConfig`, registry name `usd_breadth_usdcad`.
Reads **reference symbols** (EURUSD, GBPUSD, USDJPY, AUDUSD, NZDUSD, USDCHF) while trading another
(USDCAD): `docs/design/multi-symbol.md` > A (opt-in `on_market_candle`, one execution symbol, reference
data only through a snapshot bounded by the current engine time). Cannot run before multi-symbol step 1a.
Grid: `research/grids/usd_breadth_usdcad.toml` (marked do not run before integration).

## Source and prior

Bank of Canada Staff Analytical Note 2016-2, "Commodity Prices and the Canadian Dollar"
(opened working paper copy [FB3-7-2016-2-eng.pdf](https://publications.gc.ca/collections/collection_2016/banque-bank-canada/FB3-7-2016-2-eng.pdf);
`knowledge/research/reports/2026-11-10_idea_harvest_multisymbol.md`, idea 8): documents that a multilateral
US dollar factor has stronger predictive power for the Canadian dollar than individual commodity factors.
However, the study explicitly analyzes contemporaneous relationships, not an empirical proof of a lagged,
tradable signal. No claimed profit for a delayed rule.
Label SPECULATIVE.

Mechanism: Global macro news (Federal Reserve monetary policy, US inflation and employment, global risk
sentiment) primarily drives broad US dollar strength or weakness across all major currency pairs. If dollar
information diffuses at different speeds across currencies—specifically if CAD lags the primary European and
Asian majors due to regional hedging schedules or commodity focus—a strong broad USD breadth move across the
other six majors may predict USDCAD continuation over the subsequent day.
Prior: Modern foreign exchange markets operate with near-frictionless high-frequency arbitrage. Broad dollar
re-pricing is almost entirely absorbed intraminute across the major currency pairs. A contemporaneous daily
correlation does not imply a delayed tradable edge after costs. USDCAD trades with a spread of 5.1e-5, $5/lot
commission, slippage, and overnight swap. Typical absolute 24-hour CAD move is 20–100 bp against 1–2 bp round-trip
costs plus swap. The signed gross directional edge of a delayed breadth signal is unproven. Counted as a new
hypothesis, 8 cells, in the trial log.

## Rule and definitions

Base timeframe **1m**. Higher timeframe clock: **D1** (signal evaluation and Wilder ATR stop, constructed
from 21:00 UTC daily boundaries). All clock times are in **UTC**.

- **Active signal window:** Daily evaluation at **21:00 UTC** on weekdays (Monday through Friday),
  corresponding to the standard daily close defined in the harvest report.
- **Reference universe:** Exactly six USD majors: EURUSD, GBPUSD, AUDUSD, NZDUSD, USDJPY, USDCHF.
  The traded target USDCAD is strictly excluded from the breadth metric.
- **Signal calculation:** At each 21:00 UTC daily close `t`, calculate the one-day log return of the USD
  for each of the six reference pairs `i`:
  - For pairs quoted as foreign currency per USD (USDJPY, USDCHF):
    `r_USD,i = +100 * ln(C_{i,t} / C_{i,t-1})`
    (price rise means USD appreciated).
  - For pairs quoted as USD per foreign currency (EURUSD, GBPUSD, AUDUSD, NZDUSD):
    `r_USD,i = -100 * ln(C_{i,t} / C_{i,t-1})`
    (price rise means USD depreciated; minus the return represents USD strength).
  Where `C_{i,t}` is the close of the daily bar closing at `t` and `C_{i,t-1}` is the close of the previous
  completed daily bar (21:00 UTC 24 hours earlier, or Friday 21:00 UTC for Monday).
  All six pairs must exist and have valid closed daily bars; if any of the six pairs is missing a bar, no signal
  and no trade (no fallback, no partial universe). Reference data are read only through the bounded snapshot
  up to `now`; nothing after `now` is visible.
  - Mean USD breadth return:
    `R_USD = (r_USD,EURUSD + r_USD,GBPUSD + r_USD,AUDUSD + r_USD,NZDUSD + r_USD,USDJPY + r_USD,USDCHF) / 6`.
  - Vote count:
    `votes_up = count(r_USD,i > 0)` across the 6 pairs.
    `votes_down = count(r_USD,i < 0)` across the 6 pairs.
- **Entry:**
  - Direction **long** USDCAD if `votes_up >= min_votes` (default 4) and `R_USD >= +threshold`.
  - Direction **short** USDCAD if `votes_down >= min_votes` (default 4) and `R_USD <= -threshold`.
  - Otherwise flat (no trade).
  Entry occurs at the close of the matching USDCAD daily candle at 21:00 UTC (fills at close / open of next
  candle per engine rules). All seven symbols' daily bars (6 reference + 1 traded) must have closed.
- **Exit:** Timed exit after `hold_minutes` (720 minutes = next 09:00 UTC London morning, or 1440 minutes = next 21:00 UTC
  daily close), or when the stop loss is hit.
- **Stop:** `stop_atr` x USDCAD daily ATR(14) from entry price, placed against the trade direction, no target.
  If SL is touched within a candle: engine rules apply (SL hit first).
- **Daily ATR:** Wilder ATR(14) of USDCAD daily bars, using only completed daily sessions finished before the entry
  candle closes. No trade until 14 sessions exist.
- **Position concurrency:** Exactly **one position at a time** (no overlapping trades). If a position is currently open
  in USDCAD, any subsequent daily signal is ignored until the position has completely exited.

## Calendars and session clocks

- Daily bars close at **21:00 UTC** on weekdays, constructed from M1 candles; weekend stubs are omitted.
- FX markets trade continuously from Sunday 21:00/22:00 UTC to Friday 21:00/22:00 UTC.
- Daily rollover occurs at **17:00 America/New_York**. Positions held for 1440 minutes (24 hours) cross 17:00 NY and
  incur overnight swap, with triple swap on Wednesday (`swap_triple_weekday = WEDNESDAY`).
- Weekend handling: Signals triggered at Friday 21:00 UTC hold through the weekend until the exit time on Monday or
  stop.
- Bank holidays and missing data: If any of the six reference pairs or USDCAD is missing a daily candle at the 21:00 UTC
  mark, the setup is aborted and no trade is taken.

## Cells (pre-registered, 8)

Threshold {0.15 %, 0.20 %} x stop {1.0, 1.5} daily ATR x hold {720 min, 1440 min} = 8 cells (with `min_votes = 4` fixed in base).
**Primary cell: 0.20 % / 1.5 ATR / 1440 min** (the harvest report idea 8 rule exactly: mean return >= 0.20 %, 4 votes, 1.5 ATR stop, exit next daily close).
The other 7 cells are pre-registered robustness checks, never replacements for a failed primary.
Traded symbol: USDCAD; reference symbols: EURUSD, GBPUSD, USDJPY, AUDUSD, NZDUSD, USDCHF.

## Control

The same USDCAD entry window and holding durations (entry at 21:00 UTC, same exit duration and stop) on
**all eligible trading days**, direction fixed, never a coin flip: an all-days **long** and an all-days
**short** baseline (grid family C).
For Gate 3, the dates and timestamps of the signal cell's trades are removed from both baselines (disjoint samples).
Each signal trade is compared with the baseline of its own direction on the remaining instances, weighted by the
signal trade mix (`n_long`, `n_short`):
`control_mean = (n_long * mean_long_baseline + n_short * mean_short_baseline) / (n_long + n_short)`.
Reason: a long signal in a strengthening USD environment must beat plain "long at 21:00 UTC", so broader macro
currency drift cannot masquerade as signal edge.

## Gates (fixed before any run)

Development period only (`--dev-only`; USDCAD and all 6 reference symbols histdata development window **2015-01-02..2021-09-13**).
Reported per cell; the user decides. The family passes only if its **primary cell** passes all seven
timed_hold-style gates (`tools/timed_hold_gates.py`):

1. **Net R > 0** at normal costs and with every cost component doubled (spread, slippage, commission, swap).
2. **Halves:** net R > 0 in both halves of the development period (split at 2018-05-08, the midpoint of the
   development trade dates).
3. **Effect, not drift:** mean net R per trade of the signal cell minus the matched control mean (see Control),
   circular block bootstrap of each series independently (blocks of 5 trades, 10,000 resamples, seed 2026110),
   2.5 % quantile of the difference > 0.
4. **Breadth:** Leave-one-out breadth test (5 of 6 pairs with min 3 votes -> USDCAD) or cross-pair breadth test
   (same USD breadth applied to AUDUSD or USDCHF): net R > 0.
5. **Best-date removal:** net R stays > 0 without the 5 best trade dates.
6. **Minimum trades:** 200 on the primary cell (fewer = "not enough evidence", not a pass). Pre-estimate:
   USD breadth moves >= 0.20 % with at least 4/6 votes occur roughly 30–80 times per year x 6.7 years = 200–500 instances;
   if filtering reduces it below 200, reports "not enough evidence" and never gates.
7. **Data integrity:** count trades with more than 5 consecutive missing M1 minutes in `(entry, exit]` on
   USDCAD, a missing exit candle, or an invalid present candle. Also counted and reported: signal evaluation
   days where any of the 6 reference symbols is missing.

Multiple testing: the 8 cells are counted in the trial log (hypothesis 18 overall); raw one-sided p of
mean net R per trade reported per cell next to family-wise level 0.05 / 5 hypotheses = 0.01.
Falsified if the primary mean net R per trade <= 0, or its bootstrap 2.5 % lower bound <= 0, or Gate 3 fails.
Costs: USDCAD histdata uses FTMO parameters (spread 5.1e-5, slippage 1.5e-5, commission $5.00/lot round turn,
swap long +0.4792, swap short -8.4426 per lot). Gate 1 doubles every component. Long and short trades reported
separately (`by_direction`).
Nothing is reported as profitable before the gates. One-time test (2021-09-14 onward, MT5): only on the
user's explicit go.

## Data facts (checked 2026-11-10)

- USDCAD histdata cache: `data/cache/histdata/USDCAD/` contains annual directories `2015` through `2021`
  (earliest `2015-01-02.parquet`, last `2021-12-31.parquet`).
- Reference pairs histdata cache:
  - `data/cache/histdata/EURUSD/`: annual directories `2015` through `2021`
  - `data/cache/histdata/GBPUSD/`: annual directories `2015` through `2026`
  - `data/cache/histdata/USDJPY/`: annual directories `2015` through `2021`
  - `data/cache/histdata/AUDUSD/`: annual directories `2015` through `2021`
  - `data/cache/histdata/NZDUSD/`: annual directories `2015` through `2021`
  - `data/cache/histdata/USDCHF/`: annual directories `2015` through `2021`
  All 7 symbols have common continuous coverage from `2015-01-02` through `2021-12-31`.
- Development period: `2015-01-02` to `2021-09-13` (per `AGENTS.md` rule: develop before 2021-09-14).
- None of the 7 symbols is listed in `INVALID_PERIODS` in `src/backtester/data/histdata.py`.
- MT5 cache: `data/cache/mt5/` contains all 7 symbols (`USDCAD`, `EURUSD`, `GBPUSD`, `USDJPY`, `AUDUSD`,
  `NZDUSD`, `USDCHF`) from `2010` through `2026` (reserved for the one-time test from 2021-09-14 onward).
- Costs for USDCAD in `src/backtester/engine/costs.py`:
  - `spread = 5.1e-05` (0.000051)
  - `commission_per_lot = 5.0` (USD per lot round turn)
  - `contract_size = 100_000`
  - `quote_to_usd = 0.7047`
  - `slippage = 0.000015`
  - `swap_long_per_lot = 0.4792`, `swap_short_per_lot = -8.4426`
  - `swap_triple_weekday = WEDNESDAY`
  - `reference_price = 1.39191`
  - `tick_size = 0.00001`
  - `profit_currency = "CAD"`
- Costs for the 6 reference symbols (reference only, not traded, shown for completeness):
  - EURUSD: spread 0.00002, commission 5.0, slippage 0.00001
  - GBPUSD: spread 0.00003, commission 5.0, slippage 0.000015
  - USDJPY: spread 0.0043, commission 5.0, slippage 0.0015
  - AUDUSD: spread 0.000032, commission 5.0, slippage 0.00001
  - NZDUSD: spread 0.00003, commission 5.0, slippage 0.000015
  - USDCHF: spread 0.00005, commission 5.0, slippage 0.000025

## Assumptions (conservative choices)

1. **Daily close definition:** Daily bars close at 21:00 UTC on weekdays, constructed from M1 candles.
2. **Snapshot isolation:** Reference data from the 6 USD majors are read strictly through the bounded market
   snapshot at or before `now` (21:00 UTC); no future prices or intraminute prices are visible.
3. **Signal return and breadth formula:** Log return on completed daily candles. Equal-weight mean across all 6
   reference pairs, with negative signs for EURUSD, GBPUSD, AUDUSD, NZDUSD and positive signs for USDJPY, USDCHF.
4. **Strict universe completeness:** All six reference symbols must have valid closed daily bars at `t` and `t-1`;
   if any single symbol is missing, no breadth metric is formed and no trade occurs.
5. **Target exclusion:** USDCAD is strictly excluded from the breadth metric to eliminate self-referential bias.
6. **Position concurrency:** Exactly one position in USDCAD is open at any time. Any subsequent daily signal
   occurring while a position is open is ignored.
7. **Overnight swap and weekend holding:** Positions held across 17:00 New York incur swap per engine rules;
   Wednesday rollover charges triple swap. Friday 21:00 UTC signals hold through the weekend until Monday.
8. **Daily ATR:** Wilder ATR(14) uses completed daily bars finished before the trade entry candle closes.
9. **Gate 2 split date:** 2018-05-08 is fixed from the development period midpoint, not from data.
10. **Costs:** Standard engine defaults; Gate 1 doubles all components (spread, slippage, commission, swap).

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
- S18 A missing M1 bar of any of the six reference pairs at the evaluation time aborts the day (G5). Breadth (binding) = the same breadth signal (computed without the traded pair) applied to USDCHF, own grid file.
