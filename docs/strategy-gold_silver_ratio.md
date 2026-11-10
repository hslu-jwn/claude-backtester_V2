# Strategy: Gold–silver relative-value ratio reversion

**DRAFT: needs multi-symbol step B (pairs); do not run before integration**

Spec drafted 2026-11-10 (docs only, nothing built, nothing run). Planned folder
`strategy/gold_silver_ratio/`, config `GoldSilverRatioConfig`, registry name `gold_silver_ratio`.
Executes a linked **two-leg ratio spread trade** between XAUUSD (Gold) and XAGUSD (Silver):
`docs/design/multi-symbol.md` > B (linked two-leg execution, atomic intent, and group R
normalization). Cannot run before multi-symbol step B is integrated.
Grid: `research/grids/gold_silver_ratio.toml` (marked do not run before integration).

## Source and prior

World Gold Council, "Gold safe haven versus silver wildcard" (opened publication page;
`knowledge/research/reports/2026-11-10_idea_harvest_multisymbol.md`, idea 5) and broader statistical
arbitrage literature (e.g. Krauss 2017, arxiv:2010.01157, on pairs-trading limits and parameter
instability). The cited literature notes that while gold and silver share macroeconomic fundamentals,
ratio-based pairs trading faces structural regime shifts, changing betas, and out-of-sample decay.
Label: PRACTITIONER.

Mechanism: Gold and silver share monetary, inflationary, currency-devaluation, and global geopolitical
safe-haven risk factors. When short-term speculative capital flows or event shocks push the gold-to-silver
price ratio to historical extremes relative to its trailing moving average, the dislocation is
hypothesized to mean-revert as market participants arbitrage the precious metals complex.

Prior: The gold-to-silver ratio is not stationary over multi-year horizons; it underwent multi-year
secular trends (ranging from ~40 in 2011 to >120 in early 2020). Sizing a pair at equal dollar notional
leaves residual directional beta exposure because silver exhibits substantially higher daily volatility
than gold (beta > 1.0). Furthermore, physical and CFD carrying costs create substantial headwinds:
holding long precious metals contracts incurs punitive overnight financing swap (XAUUSD swap long
-61.27 USD/lot/night, XAGUSD swap long -68.05 USD/lot/night in the FTMO cost model). Round-trip
costs on two metal CFDs are 5–20 bp of gross notional plus swap. Signed gross directional edge
after real financing and execution costs is unproven. Counted as a new hypothesis, 8 cells, in the
trial log.

## Rule and definitions

Base timeframe **1m**. Higher timeframe clock: **D1** (signal evaluation at 21:00 UTC weekday closes
and Wilder ATR stops). All clock times are in **UTC**.

- **Traded pair:** XAUUSD (Gold spot CFD) and XAGUSD (Silver spot CFD). Both symbols are traded
  simultaneously with linked group positions.
- **Active signal window:** Daily evaluation at **21:00 UTC** on weekdays (Monday through Friday),
  corresponding to the daily close.
- **Log spread calculation:** At each 21:00 UTC daily close `t`, calculate the log price ratio:
  `s_t = ln(Close_XAUUSD,t) - ln(Close_XAGUSD,t)`.
- **Rolling z-score:**
  `z_t = (s_t - mean_120) / sd_120`
  where `mean_120` and `sd_120` are the rolling sample mean and sample standard deviation of `s`
  over the most recent 120 completed, aligned weekday daily spread closes strictly prior to `t`
  (warm-up requirement: 120 aligned daily closes). Both XAUUSD and XAGUSD must have closed at `t`
  with valid data; if either candle is missing or stale, no signal is calculated.
- **Entry signal:**
  - When `z_t` crosses from inside to outside `+z_thresh` (default `+2.0`), Gold is rich relative to
    Silver: direction is **Short XAUUSD / Long XAGUSD** at equal gross USD notional (50/50).
  - When `z_t` crosses from inside to outside `-z_thresh` (default `-2.0`), Gold is cheap relative to
    Silver: direction is **Long XAUUSD / Short XAGUSD** at equal gross USD notional (50/50).
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
  If a pair position is active, subsequent daily signals are ignored until both legs are completely
  closed.

## Multi-symbol Step B conventions and decisions

This specification explicitly adopts the conventions defined in `docs/design/multi-symbol.md` > B:

1. **Group R convention:**
   The normalization basis $D$ is established at entry from causal information and frozen for the life
   of the trade:
   $$D = |q_{\text{XAUUSD}}| \cdot v_{\text{XAUUSD}}(0) \cdot d_{\text{XAUUSD}} + |q_{\text{XAGUSD}}| \cdot v_{\text{XAGUSD}}(0) \cdot d_{\text{XAGUSD}}$$
   where $q_i$ are scale-free weights representing 50/50 gross USD notional ($q_{\text{XAUUSD}} \cdot P_{\text{XAUUSD}} = q_{\text{XAGUSD}} \cdot P_{\text{XAGUSD}}$),
   $v_i(0) = 1.0$ (both XAUUSD and XAGUSD settle profit in USD), and $d_i = \text{stop\_atr} \cdot \text{ATR(14)}_i > 0$.
   Normalized leg risk weights:
   $$w_i = \frac{|q_i| \cdot v_i(0) \cdot d_i}{D}, \quad \text{with } w_{\text{XAUUSD}} + w_{\text{XAGUSD}} = 1.0$$
   Group net return:
   $$R_{\text{group\_net}} = \frac{\sum_i \text{net\_normalized\_leg\_PnL}_i}{D}$$
   Group gross return is normalized identically using gross P/L.
2. **Two-leg cost and swap convention:**
   Each leg incurs its full per-symbol costs using `src/backtester/engine/costs.py`:
   - Fixed spread scaled with price level (`spread * fill_price / reference_price`).
   - Slippage applied against market fills.
   - Commission: FTMO percentage commission per side (`commission_pct_per_side = 0.000007`, i.e. 0.0014 % round turn).
   - Rollover financing (swap) calculated per night held across 17:00 America/New_York, including
     triple swap on Wednesday (`swap_triple_weekday = WEDNESDAY`).
   All cost components are normalized to the initial dollar basis $D$. Financing accrues over each
   leg's actual elapsed holding duration.
3. **Decisions required by design settled:**
   - **Entry eligibility:** Synchronous daily alignment required. At 21:00 UTC, both XAUUSD and XAGUSD
     must report status `OK` with fresh closed bars. If either market is closed, in a holiday break,
     or missing data, the signal is aborted. A pending group expires if not filled within 5 minutes.
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
- Precious metals trade on CME Globex / OTC market hours: Sunday 23:00 UTC to Friday 22:00 UTC, with a
  daily 1-hour maintenance break (17:00–18:00 America/New_York, which corresponds to 21:00–22:00 UTC in
  US summer time and 22:00–23:00 UTC in US winter time).
- Rollover swap is applied at **17:00 America/New_York**; triple swap occurs on Wednesday.
- Weekend handling: Positions held over the weekend remain open and accrue financing per exchange
  rules.

## Cells (pre-registered, 8)

Threshold $z_{\text{thresh}} \in \{1.75, 2.0\} \times \text{stop\_atr} \in \{1.5, 2.0\} \times \text{max\_hold\_days} \in \{15, 20\} = 8$ cells (with lookback fixed at 120 days).
**Primary cell: $z_{\text{thresh}} = 2.0$ / stop = 1.5 ATR / max hold = 20 days** (the harvest report idea 5 rule exactly).
The other 7 cells are pre-registered robustness checks, never replacements for a failed primary.
Traded symbols: XAUUSD and XAGUSD.

## Control

The same XAUUSD / XAGUSD pair structure (entry at 21:00 UTC, same holding periods and 1.5 ATR stops)
on **all eligible trading days**, direction fixed, never a coin flip: an all-days **Long XAU / Short XAG**
and an all-days **Short XAU / Long XAG** baseline (grid family C).
For Gate 3, the dates and timestamps of the signal cell's trades are removed from both baselines (disjoint
samples). Each signal trade is compared with the baseline of its own direction on the remaining instances,
weighted by the signal trade mix (`n_gold_long`, `n_gold_short`):
`control_mean = (n_gold_long * mean_long_baseline + n_gold_short * mean_short_baseline) / (n_gold_long + n_gold_short)`.
Reason: Spread divergence in precious metals must demonstrate true mean reversion rather than riding structural
secular drift in the gold/silver ratio.

## Gates (fixed before any run)

Development period only (`--dev-only`; XAUUSD and XAGUSD histdata development window **2015-01-02..2021-09-13**).
Reported per cell; the user decides. The family passes only if its **primary cell** passes all seven gates:

1. **Net group R > 0** at normal costs and with every cost component doubled (spread, slippage, commission, swap).
2. **Halves:** net group R > 0 in both halves of the development period (split at 2018-05-08).
3. **Effect, not drift:** mean net group R per trade of the signal cell minus matched control mean,
   circular block bootstrap of group trades (blocks of 5 trades, 10,000 resamples, seed 2026110),
   2.5 % quantile of the difference > 0.
4. **Sub-period stability (ex-2020 liquidity shock):** net group R > 0 excluding March–April 2020
   (2020-03-01 to 2020-04-30), ensuring the strategy does not rely exclusively on the pandemic ratio blowout.
5. **Best-date removal:** net group R stays > 0 without the 5 best trade dates.
6. **Minimum trades:** 40 group trades on the primary cell (harvest estimate: 3–15 trades/year x 6.7 years =
   20–100 trades; fewer than 40 reports "not enough evidence", not a pass).
7. **Data integrity:** count trades with missing M1 execution candles, or unresolved residual exposure after stops.

Multiple testing: The 8 cells are counted in the trial log. Raw one-sided p-values reported per cell.
Costs: XAUUSD and XAGUSD use FTMO engine parameters (`costs.py`), doubled for Gate 1. Long and short
positions reported separately (`by_direction`). One-time test (2021-09-14 onward, MT5): only on the user's
explicit authorization.

## Data facts (checked 2026-11-10)

- XAUUSD histdata cache: `data/cache/histdata/XAUUSD/` contains annual directories `2015` through `2026`.
- XAGUSD histdata cache: `data/cache/histdata/XAGUSD/` contains annual directories `2015` through `2021`.
- Neither XAUUSD nor XAGUSD is listed in `INVALID_PERIODS` in `src/backtester/data/histdata.py`.
- MT5 cache: `data/cache/mt5/XAUUSD` and `data/cache/mt5/XAGUSD` exist from `2010` through `2026`
  (reserved for the one-time test from 2021-09-14 onward).
- Engine cost parameters in `src/backtester/engine/costs.py`:
  - `XAUUSD`: `spread = 0.41`, `contract_size = 100`, `slippage = 0.10`, `commission_pct_per_side = 0.000007`,
    `swap_long_per_lot = -61.27`, `swap_short_per_lot = -4.20`, `swap_triple_weekday = WEDNESDAY`,
    `reference_price = 4342.74`, `tick_size = 0.001`, `profit_currency = USD`.
  - `XAGUSD`: `spread = 0.049`, `contract_size = 5000`, `slippage = 0.0245`, `commission_pct_per_side = 0.000007`,
    `swap_long_per_lot = -68.05`, `swap_short_per_lot = 0.30`, `swap_triple_weekday = WEDNESDAY`,
    `reference_price = 64.58`, `tick_size = 0.001`, `profit_currency = USD`.

## Assumptions (conservative choices)

1. **Daily boundary:** Daily bars are constructed with 21:00 UTC boundaries from M1 data.
2. **Equal dollar notional:** Positions are sized to 50/50 gross USD notional based on entry prices.
3. **Atomic execution:** Both legs must fill synchronously; failure to execute either cancels the group.
4. **Leg stops exit group:** When either leg touches its individual stop, the other leg exits at market at the
   next executable phase.
5. **Wilder ATR(14):** Stops use 14 completed daily sessions prior to entry.
6. **Frozen mean exit:** The mean spread level calculated at entry is frozen for the exit condition.
7. **No trade overlap:** Only one pair position is open at any time.
8. **Development period:** 2015-01-02 to 2021-09-13; split date for Gate 2 is fixed at 2018-05-08.
9. **No synthetic beta adjustment:** Uses simple equal gross dollar notional (50/50), as specified in the harvest report.
10. **Financing swap:** Metal swap costs apply at each 17:00 NY rollover, with triple swap on Wednesday.

## Decisions by Opus
