# Strategy: WTI–Brent relative-value spread reversion


**Status: pre-build screen 2026-11-12: KILLED (net -124 bp per trade; ledger P01). Not built.**
**DRAFT: needs multi-symbol step B (pairs); do not run before integration**

Spec drafted 2026-11-10 (docs only, nothing built, nothing run). Planned folder
`strategy/wti_brent_spread/`, config `WtiBrentSpreadConfig`, registry name `wti_brent_spread`.
Executes a linked **two-leg spread trade** between USOIL (WTI) and UKOIL (Brent):
`docs/design/multi-symbol.md` > B (linked two-leg execution, atomic intent, and group R
normalization). Cannot run before multi-symbol step B is integrated.
Grid: `research/grids/wti_brent_spread.toml` (marked do not run before integration).

## Source and prior

J.P. Morgan Center for Commodities (GCARD Summer 2018, pp. 77–80), "Commodity pairs and
data-snooping review" (opened publication copy; `knowledge/research/reports/2026-11-10_idea_harvest_multisymbol.md`,
idea 3). The cited review notes that an in-sample Brent–WTI rule generated an annualized excess
return of 17.6 % across a search of hundreds of parameter variations. However, the study
prominently highlights data-snooping bias and warns that out-of-sample performance frequently decays.
Label: PUBLISHED.

Mechanism: WTI (light sweet crude delivering at Cushing, Oklahoma) and Brent (North Sea light sweet
crude, global seaborne benchmark) share broad macro petroleum supply, demand, OPEC+ policy, and
refining demand drivers. The relative price spread fluctuates around an equilibrium reflecting
transportation costs, pipeline capacity, regional storage, and export economics (notably following
the late-2015 repeal of the US crude export ban). Transitory pricing dislocations caused by localized
inventory reports, shipping disruptions, or temporary refinery outages are hypothesized to mean-revert.

Prior: Commodity spread reversion is subject to severe structural breaks, contract roll discontinuities,
and persistent physical divergences. WTI and Brent CFDs settle against rolling front-month futures;
unadjusted roll gaps can artificially trigger or distort spread signals. Furthermore, extreme physical
events (such as the April 2020 Cushing storage exhaustion where WTI settled at -$37.63/bbl while Brent
remained positive around $20/bbl) demonstrate that relative-value spreads can diverge violently.
Round-trip execution costs on two commodity CFD legs are substantial: 5–15 bp of gross notional
plus two-leg overnight rollover financing. Signed gross directional edge after costs is unproven.
Counted as a new hypothesis, 8 cells, in the trial log.

## Rule and definitions

Base timeframe **1m**. Higher timeframe clock: **D1** (signal evaluation at 21:00 UTC weekday closes
and Wilder ATR stops). All clock times are in **UTC**.

- **Traded pair:** USOIL (WTI crude oil CFD) and UKOIL (Brent crude oil CFD). Both symbols are
  simultaneously traded with linked positions.
- **Active signal window:** Daily evaluation at **21:00 UTC** on weekdays (Monday through Friday),
  corresponding to the daily close.
- **Price filter:** Both USOIL and UKOIL prices must be strictly positive (`USOIL > 0.0` and
  `UKOIL > 0.0`). If either instrument exhibits a nonpositive close (e.g. during extreme delivery
  distress like April 2020), no entry signal is evaluated and any open position is flagged for
  emergency closure.
- **Log spread calculation:** At each 21:00 UTC daily close `t`, calculate the log price spread:
  `s_t = ln(Close_USOIL,t) - ln(Close_UKOIL,t)`.
- **Rolling z-score:**
  `z_t = (s_t - mean_120) / sd_120`
  where `mean_120` and `sd_120` are the rolling sample mean and sample standard deviation of `s`
  over the most recent 120 completed, aligned weekday daily spread closes strictly prior to `t`
  (warm-up requirement: 120 aligned daily closes). Both USOIL and UKOIL must have closed at `t`
  with valid data; if either candle is missing or stale, no signal is calculated.
- **Entry signal:**
  - When `z_t` crosses from inside to outside `+z_thresh` (default `+2.0`), WTI is rich relative to
    Brent: direction is **Short USOIL / Long UKOIL** at equal gross USD notional (50/50).
  - When `z_t` crosses from inside to outside `-z_thresh` (default `-2.0`), WTI is cheap relative to
    Brent: direction is **Long USOIL / Short UKOIL** at equal gross USD notional (50/50).
  - Entry occurs at the close of the matching daily M1 candle closing at 21:00:00 UTC (fills at
    close / open of next candle per engine rules).
- **Exit conditions (whichever occurs first):**
  1. **Mean reversion exit:** The daily spread `s_t` crosses the frozen entry mean (`mean_120`),
     evaluated on completed daily closes at 21:00 UTC.
  2. **Timeout exit:** After `max_hold_days` completed daily bars (default 20 completed sessions)
     following entry.
  3. **Stop loss exit:** Either leg touches its individual stop price.
- **Stops:**
  Each leg has an individual initial stop placed at `stop_atr` x daily ATR(14) from its entry price:
  - Long leg stop: `entry_price - stop_atr * ATR(14)`
  - Short leg stop: `entry_price + stop_atr * ATR(14)`
  where daily ATR(14) is the Wilder ATR(14) of that specific symbol's completed daily bars.
- **Position concurrency:** Exactly **one pair position at a time** (no overlapping spread trades).
  If a spread position is active, subsequent daily signals are ignored until both legs are completely
  closed.

## Multi-symbol Step B conventions and decisions

This specification explicitly adopts the conventions defined in `docs/design/multi-symbol.md` > B:

1. **Group R convention:**
   The normalization basis $D$ is established at entry from causal information and frozen for the life
   of the trade:
   $$D = |q_{\text{USOIL}}| \cdot v_{\text{USOIL}}(0) \cdot d_{\text{USOIL}} + |q_{\text{UKOIL}}| \cdot v_{\text{UKOIL}}(0) \cdot d_{\text{UKOIL}}$$
   where $q_i$ are scale-free weights representing 50/50 gross USD notional ($q_{\text{USOIL}} \cdot P_{\text{USOIL}} = q_{\text{UKOIL}} \cdot P_{\text{UKOIL}}$),
   $v_i(0) = 1.0$ (both USOIL and UKOIL settle profit in USD), and $d_i = \text{stop\_atr} \cdot \text{ATR(14)}_i > 0$.
   Normalized leg risk weights:
   $$w_i = \frac{|q_i| \cdot v_i(0) \cdot d_i}{D}, \quad \text{with } w_{\text{USOIL}} + w_{\text{UKOIL}} = 1.0$$
   Group net return:
   $$R_{\text{group\_net}} = \frac{\sum_i \text{net\_normalized\_leg\_PnL}_i}{D}$$
   Group gross return is normalized identically using gross P/L.
2. **Two-leg cost and swap convention:**
   Each leg incurs its full per-symbol costs using `src/backtester/engine/costs.py`:
   - Fixed spread scaled with price level (`spread * fill_price / reference_price`).
   - Slippage applied against market fills.
   - Rollover financing (swap) calculated per night held across 17:00 America/New_York, including
     triple swap on Friday (`swap_triple_weekday = FRIDAY`).
   All cost components are normalized to the initial dollar basis $D$. Financing accrues over each
   leg's actual elapsed holding duration.
3. **Decisions required by design settled:**
   - **Entry eligibility:** Synchronous daily alignment required. At 21:00 UTC, both USOIL and UKOIL
     must report status `OK` with fresh closed bars and positive prices ($>0$). If either market is
     closed, holiday-halted, or missing, the signal is aborted. A pending group expires if not filled
     within 5 minutes.
   - **Atomic execution:** Atomic only. The execution coordinator must confirm simultaneous fill
     feasibility for both legs. If one leg is rejected or cannot fill, the entire group order is canceled
     immediately. No single-legged unhedged position is ever permitted to open.
   - **The other leg after a stop:** When one leg hits its price stop during an M1 candle, an immediate
     market exit order is queued for the remaining leg at the next executable phase (next M1 close/open).
     The engine does not guess an intraminute fill price from high/low extremes. If the other leg's
     market is temporarily closed or halted, it is managed as an explicit residual leg and liquidated
     at the earliest available market minute.
   - **Missing marks and end-of-data:** Stale or closed marks are valued with explicit disclosure of
     staleness. Forced liquidations cannot be backfilled. At end-of-data, any unliquidated leg is
     recorded as unresolved residual exposure rather than assuming an unobserved exit.

## Calendars and session clocks

- Daily evaluation occurs at **21:00 UTC** Monday through Friday.
- Commodity energy CFD trading hours follow CME Globex / ICE schedules, trading continuously from
  Sunday evening through Friday evening with a daily maintenance break (typically 21:00–22:00 UTC or
  22:00–23:00 UTC depending on seasonal US/European daylight saving shifts).
- Rollover swap is applied at **17:00 America/New_York**; triple swap occurs on Friday.
- Weekend handling: Positions held over the weekend remain open and accrue financing per exchange
  rules.

## Cells (pre-registered, 8)

Threshold $z_{\text{thresh}} \in \{1.75, 2.0\} \times \text{stop\_atr} \in \{1.5, 2.0\} \times \text{max\_hold\_days} \in \{15, 20\} = 8$ cells (with lookback fixed at 120 days).
**Primary cell: $z_{\text{thresh}} = 2.0$ / stop = 1.5 ATR / max hold = 20 days** (the harvest report idea 3 rule exactly).
The other 7 cells are pre-registered robustness checks, never replacements for a failed primary.
Traded symbols: USOIL and UKOIL.

## Control

The same USOIL / UKOIL pair structure (entry at 21:00 UTC, same holding periods and 1.5 ATR stops)
on **all eligible trading days**, direction fixed, never a coin flip: an all-days **Long USOIL / Short UKOIL**
and an all-days **Short USOIL / Long UKOIL** baseline (grid family C).
For Gate 3, the dates and timestamps of the signal cell's trades are removed from both baselines (disjoint
samples). Each signal trade is compared with the baseline of its own direction on the remaining instances,
weighted by the signal trade mix (`n_wti_long`, `n_wti_short`):
`control_mean = (n_wti_long * mean_long_baseline + n_wti_short * mean_short_baseline) / (n_wti_long + n_wti_short)`.
Reason: Spread divergence in oil markets must demonstrate true mean reversion rather than riding structural
drift between crude benchmarks.

## Gates (fixed before any run)

Development period only (`--dev-only`; USOIL and UKOIL histdata development window **2015-01-02..2021-09-13**).
Reported per cell; the user decides. The family passes only if its **primary cell** passes all seven gates:

1. **Net group R > 0** at normal costs and with every cost component doubled (spread, slippage, swap).
2. **Halves:** net group R > 0 in both halves of the development period (split at 2018-05-08).
3. **Effect, not drift:** mean net group R per trade of the signal cell minus matched control mean,
   circular block bootstrap of group trades (blocks of 5 trades, 10,000 resamples, seed 2026110),
   2.5 % quantile of the difference > 0.
4. **Sub-period stability (ex-2020 oil shock):** net group R > 0 excluding the extreme commodity dislocation
   window of April 2020 (2020-04-01 to 2020-04-30), ensuring the strategy does not rely solely on the
   negative oil price anomaly.
5. **Best-date removal:** net group R stays > 0 without the 5 best trade dates.
6. **Minimum trades:** 40 group trades on the primary cell (harvest estimate: 3–15 trades/year x 6.7 years =
   20–100 trades; fewer than 40 reports "not enough evidence", not a pass).
7. **Data integrity:** count trades with nonpositive prices (`<= 0`), missing M1 execution candles, or
   unresolved residual exposure after stops.

Multiple testing: The 8 cells are counted in the trial log. Raw one-sided p-values reported per cell.
Costs: USOIL and UKOIL use FTMO engine parameters (`costs.py`), doubled for Gate 1. Long and short
positions reported separately (`by_direction`). One-time test (2021-09-14 onward, MT5): only on the user's
explicit authorization.

## Data facts (checked 2026-11-10)

- USOIL histdata cache: `data/cache/histdata/USOIL/` contains annual directories `2015` through `2021`.
- UKOIL histdata cache: `data/cache/histdata/UKOIL/` contains annual directories `2015` through `2021`.
- Neither USOIL nor UKOIL is listed in `INVALID_PERIODS` in `src/backtester/data/histdata.py`.
- `IMPORT_CONFIG.explained_jumps` in `src/backtester/data/histdata.py` explicitly documents:
  - `UKOIL`: `2020-03-09` (2020 oil price war crash, Brent 45.5 -> 33.4).
  - `USOIL`: `2020-04-19`, `2020-04-21`, `2020-04-27` (April 2020 WTI negative-price week / contract roll).
- MT5 cache: `data/cache/mt5/USOIL` and `data/cache/mt5/UKOIL` exist from `2015` through `2026`
  (reserved for the one-time test from 2021-09-14 onward).
- Engine cost parameters in `src/backtester/engine/costs.py`:
  - `USOIL`: `spread = 0.08`, `contract_size = 100`, `slippage = 0.0375`, `swap_long_per_lot = 4.966`,
    `swap_short_per_lot = -22.54`, `swap_triple_weekday = FRIDAY`, `reference_price = 92.499`, `tick_size = 0.001`,
    `profit_currency = USD`.
  - `UKOIL`: `spread = 0.073`, `contract_size = 100`, `slippage = 0.0345`, `swap_long_per_lot = 6.097`,
    `swap_short_per_lot = -27.582`, `swap_triple_weekday = FRIDAY`, `reference_price = 102.245`, `tick_size = 0.001`,
    `profit_currency = USD`.

## Assumptions (conservative choices)

1. **Daily boundary:** Daily bars are constructed with 21:00 UTC boundaries from M1 data.
2. **Positive prices strictly required:** Entries and spread calculations require `USOIL > 0` and `UKOIL > 0`.
3. **Equal dollar notional:** Positions are sized to 50/50 gross USD notional based on entry prices.
4. **Atomic execution:** Both legs must fill synchronously; failure to execute either cancels the group.
5. **Leg stops exit group:** When either leg touches its individual stop, the other leg exits at market at the
   next executable phase.
6. **No roll synthetic adjustments:** The initial backtest uses the raw cached CFD price series; roll gaps
   are treated as market price changes.
7. **Wilder ATR(14):** Stops use 14 completed daily sessions prior to entry.
8. **Frozen mean exit:** The mean spread level calculated at entry is frozen for the exit condition.
9. **No trade overlap:** Only one pair position is open at any time.
10. **Development period:** 2015-01-02 to 2021-09-13; split date for Gate 2 is fixed at 2018-05-08.

## Decisions by Opus
