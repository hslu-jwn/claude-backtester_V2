# Strategy 17: Oil shock -> CAD next day (oil-to-CAD lead-lag)

Spec drafted 2026-11-10 (docs only, nothing built, nothing run). Planned folder
`strategy/oil_cad_leadlag/`, config `OilCadLeadlagConfig`, registry name `oil_cad_leadlag`.
Reads a **reference symbol** (USOIL) while trading another (USDCAD): `docs/design/multi-symbol.md` > A
(opt-in `on_market_candle`, one execution symbol, reference data only through a snapshot bounded by the
current engine time). Cannot run before multi-symbol step 1a.
Grid: `research/grids/oil_cad_leadlag.toml` (marked do not run before integration).

## Source and prior

Bank of Canada Staff Analytical Note 2016-2, "Commodity Prices and the Canadian Dollar"
(opened working paper copy [FB3-7-2016-2-eng.pdf](https://publications.gc.ca/collections/collection_2016/banque-bank-canada/FB3-7-2016-2-eng.pdf);
`knowledge/research/reports/2026-11-10_idea_harvest_multisymbol.md`, idea 9): discusses historical daily
predictability but explicitly studies contemporaneous relationships between commodity prices and CAD.
Contemporaneous relations cannot be traded after the fact. No claimed profit for a delayed rule.
Label SPECULATIVE.

Mechanism: Crude oil is Canada's primary export commodity. A significant oil price shock alters Canada's
terms of trade, trade balance, and real income expectations. If capital flows and portfolio adjustments
diffuse gradually into foreign exchange order flow, CAD may experience a delayed continuation into the next
trading day.
Prior: Modern macro markets are highly efficient and liquid: oil price shocks are rapidly absorbed into
USDCAD intraminute or intraday by algorithmic market makers. A contemporaneous daily correlation between
oil and CAD is widely documented, but a delayed, cost-clearing directional drift over the subsequent 24 hours
faces substantial friction: USDCAD carries a spread of 5.1e-5, $5/lot commission, slippage, and overnight
financing (long swap +0.48 USD/lot, short swap -8.44 USD/lot per night, triple swap Wednesday). The typical
absolute daily CAD move is 20–100 bp against 1–2 bp round-trip costs plus swap. The signed gross directional
edge of a delayed daily rule is unproven. Counted as a new hypothesis, 8 cells, in the trial log.

## Rule and definitions

Base timeframe **1m**. Higher timeframe clock: **D1** (signal evaluation and Wilder ATR stop, constructed
from 21:00 UTC daily boundaries). All clock times are in **UTC**.

- **Active signal window:** Daily evaluation at **21:00 UTC** on weekdays (Monday through Friday),
  corresponding to the standard daily close defined in the harvest report.
- **Signal calculation:** At each 21:00 UTC daily close `t`, calculate the USOIL daily percentage return:
  `r = 100 * (C_t / C_{t-1} - 1)` in percent, where `C_t` is the close of the USOIL daily bar closing at `t`
  and `C_{t-1}` is the close of the prior completed daily bar (21:00 UTC 24 hours earlier, or Friday 21:00 UTC
  for a Monday close). Both bars must exist and must have strictly positive prices (`C > 0`, `O > 0`, `H > 0`, `L > 0`).
  If either candle is missing or nonpositive (e.g. April 2020 WTI negative price / roll jump), no signal and no trade
  (no fallback). Reference data are read only through the bounded snapshot up to `now`; nothing after `now` is visible.
- **Entry:** Directional logic reflects the inverse economic relationship between oil and USDCAD:
  - If `r >= +threshold`: direction **short** USDCAD (higher oil price implies CAD appreciation).
  - If `r <= -threshold`: direction **long** USDCAD (lower oil price implies CAD depreciation).
  - Otherwise flat (no trade).
  Entry occurs at the close of the matching USDCAD daily candle at 21:00 UTC (fills at close / open of next candle
  per engine rules). Both USOIL and USDCAD daily bars must have closed.
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
- FX markets trade continuously from Sunday 21:00/22:00 UTC to Friday 21:00/22:00 UTC. Energy CFDs (USOIL) trade
  on CME Globex hours with a daily 1-hour maintenance break (17:00–18:00 America/New_York).
- Daily rollover occurs at **17:00 America/New_York**. Positions held for 1440 minutes (24 hours) cross 17:00 NY and
  incur overnight swap, with triple swap on Wednesday (`swap_triple_weekday = WEDNESDAY`).
- Weekend handling: Signals triggered at Friday 21:00 UTC hold through the weekend until the exit time on Monday or
  stop. (Swap and weekend gap risks apply).
- US bank holidays (Thanksgiving, Christmas, New Year, Independence Day, etc.) with early market closes or trading halts
  on USOIL are handled conservatively: if any required daily bar on USOIL or USDCAD is missing, no trade is taken.
- Negative oil prices and contract rolls: Any USOIL bar with nonpositive prices (`<= 0`) or documented contract roll
  discontinuities (specifically April 2020) is rejected; no trade is triggered.

## Cells (pre-registered, 8)

Threshold {1.5 %, 2.0 %} x stop {1.0, 1.5} daily ATR x hold {720 min, 1440 min} = 8 cells.
**Primary cell: 2.0 % / 1.5 ATR / 1440 min** (the harvest report idea 9 rule exactly).
The other 7 cells are pre-registered robustness checks, never replacements for a failed primary.
Traded symbol: USDCAD; reference symbol: USOIL.

## Control

The same USDCAD entry window and holding durations (entry at 21:00 UTC, same exit duration and stop) on
**all eligible trading days**, direction fixed, never a coin flip: an all-days **long** and an all-days
**short** baseline (grid family C).
For Gate 3, the dates and timestamps of the signal cell's trades are removed from both baselines (disjoint samples).
Each signal trade is compared with the baseline of its own direction on the remaining instances, weighted by the
signal trade mix (`n_long`, `n_short`):
`control_mean = (n_long * mean_long_baseline + n_short * mean_short_baseline) / (n_long + n_short)`.
Reason: a short signal in a strengthening CAD environment (or rising USD trend) must beat plain "short at 21:00 UTC",
so broader macro currency drift cannot masquerade as signal edge.

## Gates (fixed before any run)

Development period only (`--dev-only`; USDCAD and USOIL histdata development window **2015-01-02..2021-09-13**).
Reported per cell; the user decides. The family passes only if its **primary cell** passes all seven
timed_hold-style gates (`tools/timed_hold_gates.py`):

1. **Net R > 0** at normal costs and with every cost component doubled (spread, slippage, commission, swap).
2. **Halves:** net R > 0 in both halves of the development period (split at 2018-05-08, the midpoint of the
   development trade dates).
3. **Effect, not drift:** mean net R per trade of the signal cell minus the matched control mean (see Control),
   circular block bootstrap of each series independently (blocks of 5 trades, 10,000 resamples, seed 2026110),
   2.5 % quantile of the difference > 0.
4. **Breadth:** UKOIL (Brent crude) as alternative commodity reference symbol (UKOIL daily shock -> USDCAD next day,
   same 2.0 % / 1.5 ATR / 1440 min rule): net R > 0; or CADJPY as alternative cross.
5. **Best-date removal:** net R stays > 0 without the 5 best trade dates.
6. **Minimum trades:** 200 on the primary cell (fewer = "not enough evidence", not a pass). Pre-estimate:
   USOIL daily moves >= 2.0 % occur roughly 40–70 times per year x 6.7 years = 250–450 instances; if filtering
   reduces it below 200, reports "not enough evidence" and never gates.
7. **Data integrity:** count trades with more than 5 consecutive missing M1 minutes in `(entry, exit]` on
   USDCAD, a missing exit candle, or an invalid present candle. Also counted and reported: signal evaluation
   days where a USOIL daily bar is missing, nonpositive, or affected by a contract roll jump.

Multiple testing: the 8 cells are counted in the trial log (hypothesis 17 overall); raw one-sided p of
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
- USOIL histdata cache: `data/cache/histdata/USOIL/` contains annual directories `2015` through `2021`
  (earliest `2015-01-02.parquet`, last `2021-12-31.parquet`).
- UKOIL histdata cache (breadth reference leg): `data/cache/histdata/UKOIL/` contains annual directories `2015` through `2021`.
- Development period: `2015-01-02` to `2021-09-13` (per `AGENTS.md` rule: develop before 2021-09-14).
- Neither USDCAD nor USOIL is listed in `INVALID_PERIODS` in `src/backtester/data/histdata.py`.
- USOIL continuity exemptions in `src/backtester/data/histdata.py` (`ImportConfig.explained_jumps`):
  - `2020-04-19`: "April 2020 WTI negative-price week / contract roll"
  - `2020-04-21`: "day after WTI settled negative (2020-04-20), -34 %"
  - `2020-04-27`: "WTI collapse continues after the negative settle, -26 %"
  Spec rule explicitly rejects nonpositive prices (`<= 0`) and roll-discontinuity dates.
- MT5 cache: `data/cache/mt5/USDCAD` and `data/cache/mt5/USOIL` exist from `2010` through `2026`
  (reserved for the one-time test from 2021-09-14 onward).
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
- Costs for USOIL (reference symbol, not traded, shown for completeness):
  - `spread = 0.08`
  - `contract_size = 100`
  - `slippage = 0.0375`
  - `reference_price = 92.499`
  - `tick_size = 0.001`

## Assumptions (conservative choices)

1. **Daily close definition:** Daily bars close at 21:00 UTC on weekdays, constructed from M1 candles.
2. **Snapshot isolation:** Reference data from USOIL are read strictly through the bounded market
   snapshot at or before `now` (21:00 UTC); no future prices or intraminute prices are visible.
3. **Signal return:** Percentage return `100 * (C_t / C_{t-1} - 1)` on completed 21:00 UTC daily bars.
   Equality at the threshold (`>=` and `<=`) triggers entry.
4. **Nonpositive oil prices and contract rolls:** Any USOIL bar with price <= 0 or roll jump
   (such as the April 2020 negative settlement period) is skipped; no trade is triggered.
5. **Missing candles:** If either boundary candle on USOIL or the entry candle on USDCAD is missing,
   no signal is emitted and no trade occurs.
6. **Position concurrency:** Exactly one position in USDCAD is open at any time. Any subsequent daily
   signal occurring while a position is open is ignored.
7. **Overnight swap and weekend holding:** Positions held across 17:00 New York incur swap per engine rules;
   Wednesday rollover charges triple swap. Friday 21:00 UTC signals hold through the weekend until Monday.
8. **Daily ATR:** Wilder ATR(14) uses completed daily bars finished before the trade entry candle closes.
9. **Gate 2 split date:** 2018-05-08 is fixed from the development period midpoint, not from data.
10. **Costs:** Standard engine defaults; Gate 1 doubles all components (spread, slippage, commission, swap).

## Decisions by Opus
