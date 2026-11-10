# Strategy 16: BTC impulse -> ETH delayed continuation (cross-crypto lead-lag)

Spec drafted 2026-11-10 (docs only, nothing built, nothing run). Planned folder
`strategy/btc_eth_leadlag/`, config `BtcEthLeadlagConfig`, registry name `btc_eth_leadlag`.
Reads a **reference symbol** (BTCUSD) while trading another (ETHUSD): `docs/design/multi-symbol.md` > A
(opt-in `on_market_candle`, one execution symbol, reference data only through a snapshot bounded by the
current engine time). Cannot run before multi-symbol step 1a.
Grid: `research/grids/btc_eth_leadlag.toml` (marked do not run before integration).

## Source and prior

Chernoff, "BTC/ETH price discovery" (MDPI JRFM 1911-8074/19/9/678, opened;
`knowledge/research/reports/2026-11-10_idea_harvest_multisymbol.md`, idea 12): investigates high-frequency
Granger causality and price discovery between Bitcoin and Ethereum. Finds that Granger results depend
heavily on the metric chosen, and specifically finds **no delayed cross-asset adjustment after extreme shocks**.
This provides direct contrary evidence from the academic literature, not positive support for a profitable
delayed-continuation strategy. The study's sample (2022–2025) also overlaps the reserved test era.
Label SPECULATIVE.

Mechanism: Extreme information flow or liquidity shocks in crypto may originate in Bitcoin (the dominant
asset by market capitalization, institutional liquidity, and derivatives depth) and propagate with a delay
into Ethereum order books.
Prior: Strong contrary evidence: modern crypto markets adjust across assets within milliseconds to seconds,
meaning any delayed momentum over a multi-hour holding window is likely non-existent or swamped by adverse
selection. Furthermore, CFD trading costs on FTMO are substantial: 3.25 bp commission per side (6.5 bp round-turn),
a median spread of 0.66 USD (on ~2,500 USD ETH), slippage, and an annual swap rate of -30 %/year on both long
and short positions. The absolute 4-hour ETH move is 50–300 bp, but after round-trip costs and overnight financing,
the gross conditional edge is highly uncertain. Counted as a new hypothesis, 8 cells, in the trial log.

## Rule and definitions

Base timeframe **1m**. Higher timeframe clock: **H1** (signal evaluation) and **D1** (Wilder ATR stop).
All clock times are in **UTC**.

- **Active signal window:** Continuous 24/7 evaluation across all UTC hours (**00:00–23:00 UTC**), evaluated
  at each completed UTC H1 candle close (00:00, 01:00, ..., 23:00 UTC).
- **Signal calculation:** At each qualifying H1 close `t`, calculate the BTCUSD one-hour return:
  `r = 100 * (C_t / C_{t-1} - 1)` in percent, where `C_t` is the close of the BTCUSD candle closing at `t`
  and `C_{t-1}` is the close of the candle closing 60 minutes earlier (`t - 1h`). Both candles must exist;
  if either candle is missing, no signal and no trade (no fallback). Reference data are read only through the
  bounded snapshot up to `now`; nothing after `now` is visible.
- **Entry:** Direction **long** if `r >= +threshold`, **short** if `r <= -threshold`, otherwise flat (no trade).
  Entry occurs at the close of the matching ETHUSD M1 candle closing at the H1 mark (e.g. 14:00:00 UTC).
  Fills at close / open of next candle per engine rules. Both BTCUSD and ETHUSD H1 candles must have closed.
- **Exit:** Timed exit after `hold_minutes` (180 or 240 minutes: candle closing at `entry_time + hold_minutes`),
  or when the stop loss is hit.
- **Stop:** `stop_atr` x ETHUSD daily ATR(14) from entry price, placed against the trade direction, no target.
  If SL is touched within a candle: engine rules apply (SL hit first).
- **Daily ATR:** Wilder ATR(14) of ETHUSD daily candles (using completed 00:00–24:00 UTC sessions finished
  before the entry candle closes). No trade until 14 completed sessions exist.
- **Position concurrency:** Exactly **one position at a time** (no overlapping trades). If a position is
  currently open in ETHUSD, any subsequent H1 signal is ignored until the position has completely exited.
- **Costs and financing:** Uses FTMO MT5 crypto CFD costs: commission 3.25 bp per side (0.000325), swap -30 %/year
  on both longs and shorts (`swap_long_pct_year = -0.30`, `swap_short_pct_year = -0.30`), spread 0.66, contract
  size 10, slippage 0.30.

## Calendars and session clocks

- Crypto spot and perpetual markets trade 24/7/365 without scheduled market closures.
- On FTMO MT5, ETHUSD and BTCUSD are CFDs: in early cache years (2018–2020), Saturday trading was paused on the
  broker's feed (as verified in `data/cache/mt5/ETHUSD/2018`), whereas from 2021 onwards quotes run continuously
  7 days a week.
- Daily rollover occurs at **17:00 America/New_York** (21:00 UTC in summer, 22:00 UTC in winter). Any position open
  across 17:00 NY incurs swap at -30 %/year, with triple swap on Friday (`swap_triple_weekday = FRIDAY`).
- Missing candles or broker maintenance pauses: if either the BTCUSD signal candles or the ETHUSD entry/exit
  candles are missing (such as weekend gaps in 2018–2020), no trade is executed.

## Cells (pre-registered, 8)

Threshold {1.5 %, 2.0 %} x stop {1.0, 1.5} daily ATR x hold {180 min, 240 min} = 8 cells.
**Primary cell: 2.0 % / 1.5 ATR / 240 min** (the harvest report idea 12 rule exactly).
The other 7 cells are pre-registered robustness checks, never replacements for a failed primary.
Traded symbol: ETHUSD; reference symbol: BTCUSD.

## Control

The same ETHUSD entry window and holding durations (entry at each eligible H1 close, same exit time and stop)
on **all eligible trading periods**, direction fixed, never a coin flip: an all-days **long** and an all-days
**short** baseline (grid family C).
For Gate 3, the timestamps of the signal cell's trades are removed from both baselines (disjoint samples).
Each signal trade is compared with the baseline of its own direction on the remaining instances, weighted
by the signal trade mix (`n_long`, `n_short`):
`control_mean = (n_long * mean_long_baseline + n_short * mean_short_baseline) / (n_long + n_short)`.
Reason: a long signal in a crypto bull market must beat plain "long at H1 close", so the persistent upward drift
of crypto cannot count as signal.

## Gates (fixed before any run)

Development period only (`--dev-only`; ETHUSD and BTCUSD MT5 development window **2018-01-10..2021-09-13**).
Reported per cell; the user decides. The family passes only if its **primary cell** passes all seven
timed_hold-style gates (`tools/timed_hold_gates.py`):

1. **Net R > 0** at normal costs and with every cost component doubled (commission doubled to 6.5 bp per side,
   swap doubled to -60 %/year, spread doubled to 1.32, slippage doubled to 0.60).
2. **Halves:** net R > 0 in both halves of the development period (split at 2019-11-12, the midpoint of the
   development trade dates).
3. **Effect, not drift:** mean net R per trade of the signal cell minus the matched control mean (see Control),
   circular block bootstrap of each series independently (blocks of 5 trades, 10,000 resamples, seed 2026110),
   2.5 % quantile of the difference > 0.
4. **Breadth:** Net R > 0 on Binance perpetual data (`BTCUSDT` -> `ETHUSDT`) across the overlapping development
   window (2020-01-01..2021-09-13) using actual funding and taker fees (0.05 % per side), or symmetric lead-lag
   (ETH -> BTC).
5. **Best-date removal:** net R stays > 0 without the 5 best trade dates.
6. **Minimum trades:** 200 on the primary cell (fewer = "not enough evidence", not a pass). Pre-estimate:
   a 2.0 % H1 impulse on BTCUSD over ~3.7 development years may generate fewer than 200 non-overlapping trades;
   if so, it reports "not enough evidence" and never gates.
7. **Data integrity:** count trades with more than 5 consecutive missing M1 minutes in `(entry, exit]` on
   ETHUSD, a missing exit candle, or an invalid present candle. Also counted and reported: signal evaluation
   hours where a BTCUSD signal candle is missing.

Multiple testing: the 8 cells are counted in the trial log (hypothesis 16 overall); raw one-sided p of
mean net R per trade reported per cell next to family-wise level 0.05 / 5 hypotheses = 0.01.
Falsified if the primary mean net R per trade <= 0, or its bootstrap 2.5 % lower bound <= 0, or Gate 3 fails.
Costs: ETHUSD uses FTMO crypto CFD parameters (commission 3.25 bp per side, swap -30 %/year, spread 0.66).
Gate 1 doubles every component. Long and short trades reported separately (`by_direction`).
Nothing is reported as profitable before the gates. One-time test (2021-09-14 onward, MT5): only on the
user's explicit go.

## Data facts (checked 2026-11-10)

- ETHUSD MT5 cache: `data/cache/mt5/ETHUSD/` starts on `2018-01-10` (`data/cache/mt5/ETHUSD/2018/2018-01-10.parquet`
  is the earliest file). Annual folders exist through `2026`.
- BTCUSD MT5 cache: `data/cache/mt5/BTCUSD/` starts on `2017-04-06` (`data/cache/mt5/BTCUSD/2017/2017-04-06.parquet`
  is the earliest file). Annual folders exist through `2026`.
- Histdata cache: neither BTCUSD nor ETHUSD is present in histdata (crypto history is provided exclusively via MT5 and Binance).
- Binance cache: `data/cache/binance/BTCUSDT` and `data/cache/binance/ETHUSDT` exist from `2020` to `2026`.
- Development period: strictly `2018-01-10` to `2021-09-13` (bounded by ETHUSD MT5 data start and the repo-wide 2021-09-14 split).
  This provides ~3.7 years of development history.
- Weekend availability: in 2018 MT5 cache, Saturday files are absent (feed was inactive on Saturdays); from 2021 onward,
  all 7 calendar days are present.
- FTMO crypto CFD costs in `src/backtester/engine/costs.py` for ETHUSD:
  - `spread = 0.66`
  - `contract_size = 10`
  - `slippage = 0.3`
  - `commission_pct_per_side = 0.000325` (FTMO_CRYPTO_COMMISSION_PCT_SIDE, i.e. 3.25 bp per side, 6.5 bp round-turn)
  - `swap_long_pct_year = -0.30` (-30 % per year)
  - `swap_short_pct_year = -0.30` (-30 % per year)
  - `swap_triple_weekday = FRIDAY`
  - `reference_price = 2498.33`, `tick_size = 0.01`.

## Assumptions (conservative choices)

1. **MT5 CFD development source:** Because histdata contains no crypto and ETHUSD MT5 cache starts 2018-01-10,
   the development period is strictly 2018-01-10 to 2021-09-13.
2. **Snapshot isolation:** Reference data from BTCUSD are read strictly through the bounded market
   snapshot at or before `now`; no future prices or intraminute prices are visible.
3. **Signal return:** Percentage return `100 * (C_t / C_{t-1} - 1)` on completed H1 candles. Equality at the
   threshold (`>=` and `<=`) triggers entry.
4. **Missing candles and weekend pauses:** If either boundary candle of the H1 window on BTCUSD or the entry candle
   on ETHUSD is missing (including weekend pauses in 2018–2020), no signal is emitted and no trade occurs.
5. **No trade overlap:** Only one position in ETHUSD is open at any time. Any subsequent signal occurring while
   a trade is active is ignored.
6. **Swap charging:** Daily rollover occurs at 17:00 America/New_York (-30 %/year charged per night, triple swap
   on Friday). Holds of 180 or 240 minutes crossing 17:00 NY are charged swap per engine rules.
7. **Daily ATR:** Wilder ATR(14) uses completed UTC daily sessions finished before the trade entry candle closes.
8. **Gate 2 split date:** 2019-11-12 is fixed from the development period midpoint, not from data.
9. **Config keys:** Proposed names (`ref_symbol`, `ref_timeframe`, `active_from`, `active_to`,
   `min_ref_return_pct`, `hold_minutes`, `direction = "with_ref"`).
10. **Costs:** Standard engine defaults; Gate 1 doubles all components (6.5 bp commission per side, -60 %/year swap).

## Decisions by Opus
