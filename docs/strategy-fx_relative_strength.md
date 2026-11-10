# Strategy: Weekly currency relative-strength cross (FX momentum)

**DRAFT: needs multi-symbol step B (pairs) or C (baskets); do not run before integration**

Spec drafted 2026-11-10 (docs only, nothing built, nothing run). Planned folder
`strategy/fx_relative_strength/`, config `FxRelativeStrengthConfig`, registry name `fx_relative_strength`.
Requires **cross-sectional universe ranking** (`docs/design/multi-symbol.md` > C) across seven major
currency pairs, and linked **two-leg group execution** (`docs/design/multi-symbol.md` > B) of the top
winner and loser versus USD. Cannot run before multi-symbol steps B and C are integrated.
Grid: `research/grids/fx_relative_strength.toml` (marked do not run before integration).

## Source and prior

Menkhoff, Sarno, Schmeling, and Shang, "Currency Momentum Strategies", Journal of Financial Economics
(2012) 106(3), pp. 660–684 (opened full paper copy; [CEPR author summary](https://cepr.org/voxeu/columns/limits-currency-momentum-trading),
opened; `knowledge/research/reports/2026-11-10_idea_harvest_multisymbol.md`, idea 1). The authors document
winner-minus-loser annual excess returns up to 10 % in a broad cross-sectional currency universe (up to
48 currencies). Crucially, the authors note that transaction costs absorb 30–50 % of returns even for
institutional players. Subsequent academic replications (e.g. Hutchinson et al.) document substantial
out-of-sample decay and vulnerability to abrupt momentum crashes.
Label: PUBLISHED.

Mechanism: Cross-country information diffusion, macroeconomic divergences (growth, interest rate cycles,
terms-of-trade shifts), and persistent institutional capital rebalancing produce multi-week momentum
trends in major currency values relative to the US dollar.

Prior: Restricting the momentum universe to seven G10 majors removes the high-yielding, high-momentum
emerging market currencies that contributed heavily to published returns. Within major FX, spreads are
tight (1–2 bp round trip), but holding two legs across a full week incurs up to five days of two-leg
rollover financing (swap), which is frequently adverse on trending pairs due to carry asymmetries.
Momentum reversals during central bank surprise weeks can trigger concurrent stops on both legs.
Typical absolute weekly relative movement is 20–150 bp against 1–2 bp round-trip costs and overnight
financing. Signed gross directional edge in this restricted CFD universe is unproven. Counted as a new
hypothesis, 8 cells, in the trial log.

## Rule and definitions

Base timeframe **1m**. Higher timeframe clocks: **D1** and **W1** (constructed from 21:00 UTC daily
closes; evaluation every Friday at 21:00 UTC). All clock times are in **UTC**.

- **Universe:** Exactly seven USD major currency pairs:
  - Quoted as USD per foreign currency (direct): EURUSD, GBPUSD, AUDUSD, NZDUSD.
  - Quoted as foreign currency per USD (indirect): USDJPY, USDCHF, USDCAD.
- **Active signal window:** Every Friday at **21:00 UTC** (market close of the trading week).
- **USD return calculation:** At Friday 21:00 UTC, for each currency $i$ in the universe, calculate its
  log return in USD value over the lookback window of $K$ completed weekday daily bars strictly prior
  to the evaluation timestamp (default $K = 100$ weekday daily bars, corresponding to 20 trading weeks):
  - For direct pairs (EUR, GBP, AUD, NZD), where the exchange rate $P_i$ is USD per unit of currency:
    $$r_{i,t} = \ln(C_{i,t} / C_{i,t-K})$$
  - For indirect pairs (JPY, CHF, CAD), where the exchange rate $P_i$ is foreign currency per USD:
    $$r_{i,t} = -\ln(C_{i,t} / C_{i,t-K})$$
  All seven currency pairs must exist and have valid closed daily bars; if any single pair has missing
  data or an incomplete history, no signal is evaluated and no rebalance occurs (no partial ranking).
- **Ranking and trade selection:**
  Rank the seven currencies by $r_{i,t}$ in descending order:
  - Strongest currency ($C_{\text{winner}}$): Rank 1 (highest positive USD return).
  - Weakest currency ($C_{\text{loser}}$): Rank 7 (lowest return / highest depreciation).
  - Both legs are executed against USD at equal gross USD notional (50/50):
    - Buy $C_{\text{winner}}$ vs USD at 50 % notional:
      - If EUR/GBP/AUD/NZD: Long the pair.
      - If JPY/CHF/CAD: Short the pair.
    - Sell $C_{\text{loser}}$ vs USD at 50 % notional:
      - If EUR/GBP/AUD/NZD: Short the pair.
      - If JPY/CHF/CAD: Long the pair.
- **Entry timing:** Entry occurs at the close of the matching M1 candle at Friday 21:00:00 UTC
  (fills at close / open of next candle per engine rules).
- **Exit conditions (whichever occurs first):**
  1. **Scheduled rebalance exit:** Closed at the next Friday 21:00 UTC (1-week hold, default 5 completed
     daily sessions).
  2. **Stop loss exit:** Either leg touches its individual stop price.
- **Stops:**
  Each leg has an individual initial stop placed at `stop_atr` x daily ATR(14) from its entry price:
  - Long leg stop: `entry_price - stop_atr * ATR(14)`
  - Short leg stop: `entry_price + stop_atr * ATR(14)`
  where daily ATR(14) is the Wilder ATR(14) of that specific symbol's completed daily bars.
- **Position concurrency:** Exactly **one basket position at a time**. The old weekly basket closes at
  Friday 21:00 UTC as the new weekly basket is evaluated and entered.

## Multi-symbol Step B and C conventions and decisions

This specification explicitly adopts the conventions defined in `docs/design/multi-symbol.md` > B and C:

1. **Group R convention:**
   The normalization basis $D$ is established at entry from causal information and frozen for the life
   of the trade:
   $$D = |q_{\text{winner}}| \cdot v_{\text{winner}}(0) \cdot d_{\text{winner}} + |q_{\text{loser}}| \cdot v_{\text{loser}}(0) \cdot d_{\text{loser}}$$
   where $q_i$ are scale-free weights representing 50/50 gross USD notional, $d_i = \text{stop\_atr} \cdot \text{ATR(14)}_i$,
   and $v_i(0)$ is the causally available exchange conversion factor from the pair's profit currency to
   USD at the entry timestamp (e.g. for USDJPY, profit is in JPY and $v(0) = 1 / P_{\text{USDJPY}}$;
   for EURUSD, profit is already in USD and $v(0) = 1.0$).
   Normalized leg risk weights:
   $$w_i = \frac{|q_i| \cdot v_i(0) \cdot d_i}{D}, \quad \text{with } w_{\text{winner}} + w_{\text{loser}} = 1.0$$
   Group net return:
   $$R_{\text{group\_net}} = \frac{\sum_i \text{net\_normalized\_leg\_PnL}_i}{D}$$
   Where leg P/L in non-USD currencies is converted to USD at its actual exit timestamp before division by $D$.
2. **Two-leg cost and swap convention:**
   Each leg incurs its full per-symbol costs using `src/backtester/engine/costs.py`:
   - Fixed spread scaled with price level (`spread * fill_price / reference_price`).
   - Slippage applied against market fills.
   - Fixed commission: $5.00 per 1.0 lot round turn.
   - Rollover financing (swap) calculated per night held across 17:00 America/New_York, including
     triple swap on Wednesday (`swap_triple_weekday = WEDNESDAY`).
   All cost components are converted to USD and normalized to the initial dollar basis $D$.
3. **Decisions required by design settled:**
   - **Entry eligibility:** Strict synchronous universe eligibility. All seven currency pairs must
     have closed valid daily bars at Friday 21:00 UTC with status `OK` and complete 100-day histories.
     If any currency is unavailable, missing, or halted, the entire weekly rebalance is skipped
     (no fallback to a 6-pair ranking).
   - **Atomic execution:** Atomic only. Both the winner and loser legs must execute simultaneously.
     If either leg fails execution or is rejected, the entire group order is canceled immediately.
   - **The other leg after a stop:** When one leg hits its price stop during an M1 candle, an immediate
     market exit order is queued for the remaining leg at the next executable phase (next M1 close/open).
     The engine does not guess an intraminute fill price. If the market is closed (e.g. stop occurs at
     Friday close), the residual leg exits at the earliest available market minute when trading resumes.
   - **Missing marks and end-of-data:** Stale or closed marks value open legs with staleness disclosed.
     At end-of-data, open legs are recorded as unresolved residual exposure rather than assuming an
     unobserved liquidation.

## Calendars and session clocks

- Weekly rebalance occurs at **Friday 21:00 UTC**.
- Foreign exchange trading closes for the weekend on Friday at 22:00 UTC and reopens on Sunday at 22:00 UTC.
  Executing at Friday 21:00 UTC ensures trades fill during liquid market hours before the weekend close.
- Rollover swap applies daily at **17:00 America/New_York**; triple swap occurs on Wednesday.
- Positions held across the weekend do not accrue weekend swap (FX rollover is charged on New York weekdays).

## Cells (pre-registered, 8)

Lookback bars $\in \{80, 100\} \times \text{stop\_atr} \in \{1.5, 2.0\} \times \text{hold\_weeks} \in \{1, 2\} = 8$ cells.
(Note: 80 bars = 16 weeks, 100 bars = 20 weeks; 1 hold week = 5 daily bars, 2 hold weeks = 10 daily bars).
**Primary cell: lookback = 100 bars (20 weeks) / stop = 2.0 ATR / hold = 1 week** (the harvest report idea 1 rule exactly).
The other 7 cells are pre-registered robustness checks, never replacements for a failed primary.
Traded universe: EURUSD, GBPUSD, AUDUSD, NZDUSD, USDJPY, USDCHF, USDCAD.

## Control

A fixed directional pair baseline (grid family C): an all-weeks **Long EURUSD / Short USDJPY** basket
and an all-weeks **Short EURUSD / Long USDJPY** basket, entered every Friday at 21:00 UTC and held for
the same duration with the same stop ATR.
For Gate 3, the dates and timestamps of the signal cell's trades are removed from both baselines (disjoint
samples). Each signal trade is compared with the baseline on the remaining instances:
`control_mean = (n_long_eur * mean_long_baseline + n_short_eur * mean_short_baseline) / (n_long_eur + n_short_eur)`.
Reason: Relative-strength ranking must demonstrate cross-sectional selection skill that exceeds a static
long-EUR / short-JPY drift.

## Gates (fixed before any run)

Development period only (`--dev-only`; histdata development window **2015-01-02..2021-09-13**).
Reported per cell; the user decides. The family passes only if its **primary cell** passes all seven gates:

1. **Net group R > 0** at normal costs and with every cost component doubled (spread, slippage, commission, swap).
2. **Halves:** net group R > 0 in both halves of the development period (split at 2018-05-08).
3. **Effect, not drift:** mean net group R per trade of the signal cell minus matched control mean,
   circular block bootstrap of group trades (blocks of 5 trades, 10,000 resamples, seed 2026110),
   2.5 % quantile of the difference > 0.
4. **Breadth across currencies:** no single currency pair accounts for more than 40 % of total net group R
   generated across the strategy.
5. **Best-date removal:** net group R stays > 0 without the 5 best trade dates.
6. **Minimum trades:** 200 weekly basket trades on the primary cell (~52 weeks/year x 6.7 years = ~348 eligible
   rebalance weeks; fewer than 200 reports "not enough evidence", not a pass).
7. **Data integrity:** count weeks with missing universe candles, failed atomic fills, or unresolved residual
   exposure after stops.

Multiple testing: The 8 cells are counted in the trial log. Raw one-sided p-values reported per cell.
Costs: All 7 pairs use FTMO engine parameters (`costs.py`), doubled for Gate 1. One-time test (2021-09-14
onward, MT5): only on the user's explicit authorization.

## Data facts (checked 2026-11-10)

- All seven pairs exist in `data/cache/histdata/` with annual directories `2015` through `2021`:
  `EURUSD`, `GBPUSD`, `AUDUSD`, `NZDUSD`, `USDJPY`, `USDCHF`, `USDCAD`.
- None of the seven pairs is listed in `INVALID_PERIODS` in `src/backtester/data/histdata.py`.
- MT5 cache: All seven pairs exist in `data/cache/mt5/` from `2015` through `2026`
  (reserved for the one-time test from 2021-09-14 onward).
- Engine cost parameters in `src/backtester/engine/costs.py`:
  - All 7 pairs have `commission_per_lot = 5.0` USD per lot round turn and `contract_size = 100_000`.
  - `EURUSD`: `spread = 0.00002`, `slippage = 0.00001`, `swap_long_per_lot = -8.53`, `swap_short_per_lot = 0.21`,
    `reference_price = 1.15405`, `tick_size = 0.00001`, `profit_currency = USD`.
  - `GBPUSD`: `spread = 0.000059`, `slippage = 0.00002`, `swap_long_per_lot = -5.77`, `swap_short_per_lot = -4.48`,
    `reference_price = 1.348`, `tick_size = 0.00001`, `profit_currency = USD`.
  - `AUDUSD`: `spread = 0.000032`, `slippage = 0.00001`, `swap_long_per_lot = -3.04`, `swap_short_per_lot = -6.54`,
    `reference_price = 0.71185`, `tick_size = 0.00001`, `profit_currency = USD`.
  - `NZDUSD`: `spread = 0.00003`, `slippage = 0.000015`, `swap_long_per_lot = -4.78`, `swap_short_per_lot = 0.01`,
    `reference_price = 0.57601`, `tick_size = 0.00001`, `profit_currency = USD`.
  - `USDJPY`: `spread = 0.0043`, `slippage = 0.0015`, `swap_long_per_lot = 1.0813`, `swap_short_per_lot = -11.0347`,
    `reference_price = 158.058`, `tick_size = 0.001`, `profit_currency = JPY`, `quote_to_usd = 0.00632`.
  - `USDCAD`: `spread = 0.000051`, `slippage = 0.000015`, `swap_long_per_lot = 0.4792`, `swap_short_per_lot = -8.4426`,
    `reference_price = 1.39191`, `tick_size = 0.00001`, `profit_currency = CAD`, `quote_to_usd = 0.7047`.
  - `USDCHF`: `spread = 0.00005`, `slippage = 0.000025`, `swap_long_per_lot = 1.5715`, `swap_short_per_lot = -16.2468`,
    `reference_price = 0.81828`, `tick_size = 0.00001`, `profit_currency = CHF`, `quote_to_usd = 1.2088`.

## Assumptions (conservative choices)

1. **Rebalance timing:** Every Friday at 21:00 UTC, before weekend market closure.
2. **Universe completeness:** All seven pairs must be present; missing data halts the rebalance.
3. **Equal dollar notional:** Both legs sized to 50/50 gross USD notional.
4. **Atomic execution:** Both selected legs must fill synchronously; failure cancels the basket.
5. **Leg stops exit group:** When either leg touches its individual stop, the other leg exits at market at
   the next executable phase.
6. **Currency conversion:** Profit for non-USD quoted pairs (JPY, CAD, CHF) is converted using causal FX marks.
7. **Wilder ATR(14):** Stops use 14 completed daily sessions prior to entry.
8. **No carry filter:** Pure price momentum; carry differentials are not filtered or used to break ties.
9. **Tie-breaking:** Deterministic alphabetical tie-breaking on currency symbol if returns are equal.
10. **Development period:** 2015-01-02 to 2021-09-13; split date for Gate 2 is fixed at 2018-05-08.

## Decisions by Opus
