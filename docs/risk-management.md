# Risk Management & Account Simulation Module

**Goal:** turn a strategy's trades into account money, to choose a safe risk and later to estimate the chance of passing an FTMO challenge ($100k). The strategy outputs trades in **R only**; this module turns them into money. That way risk settings can be tested on one backtest run, or on the manual R log, without re-running detection.

Settings defined with the user on 2026-10-10 (replace the earlier "risk guidelines" draft). Every value is a setting (⚙️) with the default given here.

## Base backtest: account simulation over the whole period
A plain account backtest over the whole data range. **No challenge phases, no prop-firm limits** in this part (rule set by the user); those come later as an extra field (› Prop-firm field).
- **One strategy per run** (rule set by the user). No combining strategy 1 and 2 on one account.

### Account & sizing
- ⚙️ **Starting balance:** a free number field, default **100,000 USD**.
- ⚙️ **Risk per trade:** % of the **current balance** (closed trades) at the entry, default **1%**. It shrinks after losses and grows after wins.
- **Lots** = risk $ ÷ (SL distance incl. costs × value per point), from per-symbol contract specs (value per point, lot step, minimum lot); always **rounded down** to the lot step.
- **Several TPs** (strategy 2: 3 equal parts; strategy 1: TP1 share): each part is rounded down to the lot step; the **remainder goes to TP1** (rule set by the user). If the position is too small to split into all parts (less than parts × minimum lot), it trades with **fewer TPs**: the first TPs get the lots, the later ones are dropped (the last remaining TP closes the rest). Below one minimum lot → trade skipped, logged as "too small".
- The trade's R result is recalculated from the lots actually used per part.

### Intrabar execution (V2.4c T-03)

The setting `engine.intrabar` is `"m1"` by default (rule set by the user 2026-10-24; `"sl_first"` = the earlier execution),
which resolves ambiguous closed base candles from M1. See
ARCHITECTURE.md > How a backtest steps through time > Intrabar resolution for the
execution and diagnostic contract. Penetration and short ask triggering apply on M1
too; levels, partial shares and fill costs remain the same. SL still wins within an
ambiguous M1 candle. After TP1, break-even starts on the next M1 candle; on a limit's
filling M1 candle only SL counts, then TPs start on the next minute. Missing M1 falls
back conservatively and is counted. M1-base strategies keep existing behaviour.
A replayed limit records `entry_time` at its filling M1 candle's close; `entry_candle`
stays at the base candle's open. Decisions and callbacks still run at the base close,
and no exit precedes entry (Opus clarification, 2026-10-23 21:02).
The seven-strategy 2023 measurement informs a later user decision on the default.

### Costs (per symbol)
- **Tick rounding** (V2.4d item 9, Opus clarifications 2026-10-24):
  `CostConfig.round_to_tick` defaults to **True** (rule set by the user, 2026-10-26; False
  reproduces the earlier execution).
  When enabled, round strategy order levels at fill using `SymbolCosts.tick_size`;
  None disables rounding for that symbol. Market fills, gap fills at the open and M1
  replay prices remain the observed prices (including an existing gap-open fill when
  the rounded limit would lie inside that candle). Buy limits round down, sell limits up;
  long SL rounds up and long TP1-3 down (short mirrored). R uses the rounded initial
  SL distance. The cost-inclusive break-even stop rounds up for longs, down for shorts,
  preserving >= 0R net at a level hit before swap/funding (a gap may still lose).
  A level within 1e-9 price units of a tick is unchanged; penetration distances are
  thresholds and are never rounded. Pending limits must reach the rounded level and
  its penetration threshold before consumption; placement proof uses the original order.
  Orders made invalid by rounding (SL/TP on or across entry, or non-increasing TP levels
  under the existing validator) are skipped with `strategy.on_order_skipped`, counted
  and given an aggregate reason in run notes. Original invalid orders still raise.
  Per-run diagnostics count moved orders once (including rejected attempts), moved levels
  (limit entry, SL, TP1-3 and computed BE), mean absolute move in ticks over moved levels,
  and rejections. Warm-up attempts are excluded, using the entry base candle's open time.
  Panel setting / TOML grid key: `engine.costs.round_to_tick = [false, true]`.
  Per-symbol tick metadata stays in settings/presets and grids, without extra panel
  widgets, preserving the panel's existing widget-count performance limit.

  Tick snapshot, 2026-10-24: `results/trading.json` is present but contains symbol-name
  mappings, no `trade_tick_size`. FTMO fallback is 10^-digits from the cache quote
  precision table `data/sources.py:PRICE_DIGITS` (FTMO snapshot 2026-10-15 for expanded
  symbols; XAUUSD includes histdata's three-decimal precision). These are fallback
  precision estimates, not verified exchange ticks. Literal engine table; no runtime
  reads of results or data. Binance ticks are **None**, pending an exchange snapshot.

  | Symbols | Tick size | Source |
  |---|---:|---|
  | GBPUSD, EURUSD, AUDUSD, NZDUSD, EURGBP, USDCAD, USDCHF | 0.00001 | Cache digits (5) |
  | GBPJPY, USDJPY, EURJPY, XAUUSD, XAGUSD, USOIL, UKOIL, DXY, NATGAS | 0.001 | Cache digits (3) |
  | NAS100, US500, GER40, UK100, JP225, EU50, US30, US2000, BTCUSD, ETHUSD | 0.01 | Cache digits (2) |
  | BTCUSDT, ETHUSDT | None | No recorded exchange tick; rounding disabled |

  `scripts/measure_ticks.py` compares off/on on all seven golden setups for 2023 with
  current defaults and one worker, writing `results/ticks.md`, `.csv` and a run log.
  The measurement does not change the default; that decision belongs to the user.
- **Limit penetration** (V2.4d item 3, user 2026-10-23):
  `CostConfig.tp_penetration` is a finite, non-negative spread multiple, default **0.5** (rule set by
  the user 2026-10-23 after the measurement in `results/tp_penetration.md`; 0 = touch fills as before).
  With `d = tp_penetration * spread`, use the spread actually fixed for the trade at entry
  (fixed, price-scaled or table spread; zero when spread is disabled). A long TP needs
  bid high >= TP + d; a short TP needs bid low <= TP - d. Partial TPs, TP2/TP3 and the
  move to break-even after TP1 require this same fill test. Gap opens beyond the threshold
  still fill at the TP level. MAE/MFE tracking and SL-first precedence stay unchanged.
  Buy limits need low <= entry - d; sell limits need high >= entry + d. An insufficient
  penetration leaves the order pending under its existing expiry/cancellation rules.
  Existing entry gap pricing remains; test penetration against the placed limit, using
  the spread of the candidate fill (including its existing gap entry price).
- **Short TP on ask:** `CostConfig.short_tp_on_ask`, default **True** (rule set by the user 2026-10-23). When enabled,
  short TPs need bid low + the trade's spread <= TP - d and fill at TP itself, with no
  additional exit spread. When disabled, preserve bid triggering and fill at TP + spread.
  TP fills have no slippage. Both defaults reproduce existing fills exactly; the user
  chooses any future default after measuring all seven golden setups.
- **TP touch diagnostics:** `tp_levels_touched` counts each outstanding TP level once per
  trade when the old bid-touch rule reaches it. `tp_levels_touched_not_filled` counts each
  such level once if it fails the new price threshold in any candle, even if filled later.
  These are price-threshold diagnostics; SL-first precedence and the entry fill candle's
  exclusion of TPs remain in force on the execution timeframe (base by default, M1
  during intrabar resolution). Already filled levels are no longer observed.
  Both counts are written to `trades.csv`; summary `tp_touched_not_filled_share` is the
  sum of missed levels divided by the sum of touched levels (0 when none were touched).
- ⚙️ **Spread:** a **fixed value per symbol** for every pair (histdata.com has no ask prices, user 2026-10-10). Defaults (estimates until FTMO's spreads are measured): NAS100 **1.0** point, US500 **0.5** point, XAUUSD 0.25, GBPUSD 0.3 pip, GBPJPY 1.0 pip.
- ⚙️ **Spread scaled with the price level** (rule set by the user, 2026-10-16; ROADMAP 11.14): the fixed spread is today's FTMO
  value, which is far too large in R in years with lower prices (XAGUSD 2015 at about $15 against $65 now). In the fixed-spread
  mode the spread of a fill is

      spread used = SymbolCosts.spread x (fill price / SymbolCosts.reference_price)

  so it stays the same share of the price. The fill price is the trade's entry; the exit pays the same spread as the entry
  (as before). `CostConfig.spread_price_scaling` (default **True**) switches it off to reproduce old results. The spread
  table (per year and hour, ROADMAP 6.7) is a measurement and is **not** scaled; where it has no value the scaled fixed spread
  is used. **Default: the FTMO median table** (rule set by the user, 2026-10-26; re-evaluated after a period of demo
  trading), shipped as `engine/ftmo_spread_median.json` (copy of `data/spreads/ftmo_spread_median.json`, measured
  2026-10-15; XAUUSD, GBPUSD, GBPJPY 2015-2026, NAS100 / US500 2021-2026; other symbols keep the fixed spread).
  `CostConfig(spread_table=None)` gives the fixed spread. The cost filter (`max_cost_r`) and the break-even offset use the scaled spread. A symbol without a reference price
  (`reference_price = None`; the Binance symbols, which have no spread) is never scaled. Slippage follows the same entry-price
  scaling (rule set by the user, 2026-10-22; B4), independently of the spread switch/table. FX is scaled the same way (no special case).
  Reference prices (`REFERENCE_PRICES` in `engine/costs.py`): median M1 bid close over the last 60 cached days of the FTMO MT5
  history (`data/cache/mt5/<SYM>`, 2026-08-16 to 2026-10-14), measured 2026-10-16:

  | Symbol | Price | Symbol | Price | Symbol | Price |
  |---|---|---|---|---|---|
  | XAUUSD | 4342.74 | XAGUSD | 64.58 | GBPUSD | 1.348 |
  | GBPJPY | 209.75 | EURUSD | 1.15405 | AUDUSD | 0.71185 |
  | NZDUSD | 0.57601 | EURGBP | 0.85688 | USDJPY | 158.058 |
  | USDCAD | 1.39191 | USDCHF | 0.81828 | EURJPY | 179.43 |
  | NAS100 | 29580.48 | US500 | 7696.45 | GER40 | 25563.64 |
  | UK100 | 10720.5 | JP225 | 66072.5 | EU50 | 6316.47 |
  | US30 | 52172.25 | US2000 | 2890.78 | USOIL | 92.499 |
  | UKOIL | 102.245 | NATGAS | 2.876 | DXY | 99.673 |
  | BTCUSD | 79679.87 | ETHUSD | 2498.33 | | |

  Note: the XAUUSD, GBPUSD, GBPJPY, NAS100 and US500 spreads are estimates, not measured in this window; their reference price is
  still the 2026 price level they stand for.
- ⚙️ **Commission** (per lot, round turn) and ⚙️ **swap** (per lot per night, long and short): per-symbol fields, to be updated from MT5/FTMO. Commission defaults (user, 2026-10-10, as ROADMAP 3.1): XAUUSD **$6** (replaced 2026-10-15 by FTMO's percentage fee, see *Real fees* below), GBPUSD / GBPJPY **$5**, NAS100 / US500 **0**.
  Swap defaults = FTMO's MT5 rates of 2026-10-14 (rule set by the user, 2026-10-14), USD per lot per night, long / short:
  XAUUSD **-61.27 / -4.20**, GBPUSD **-5.77 / -4.48**, GBPJPY **+2.04 / -13.85** (triple Wednesday), NAS100 **-6.912 / +0.339**,
  US500 **-1.2218 / -0.4575** (triple Friday). Today's rates are applied to every year, so swap is overstated in 2020-21
  (rates near zero then).
- **Swap in the engine** (user asked for swap costs 2026-10-14; details chosen by Claude): a position open
  across the daily **rollover at 17:00 America/New_York** (FTMO server midnight) pays one night of swap
  (long or short rate, USD per 1.0 lot per night, negative = cost); on the symbol's ⚙️ `swap_triple_weekday`
  (from MT5 `swap_rollover3days`, default Wednesday) it counts 3 nights. In R:
  swap_R = nights' swap per lot / (SL distance x value of a 1.0 price move per lot). It changes **net R
  only** (gross = chart prices) and is reported as `swap_r` per trade. ⚙️ `swap_enabled` (CostConfig) switches it
  off so results can be shown with and without swap. Rates come from FTMO via `tools.mt5_info` (defaults above).
- **Costs of the symbols of ROADMAP 11.8 / 11.9** (added 2026-10-15; the five symbols above are unchanged). Source: the running FTMO MT5 terminal
  (`symbol_info`), same method as the swap defaults: swap USD per lot per night = swap points x tick value (checked: gives the stored
  XAUUSD / NAS100 values), `quote_to_usd` = tick value / (tick size x contract size) (fixed approximation, 2026-10-15 rates),
  triple weekday from `swap_rollover3days` (FX / metals Wednesday, indices / energy / crypto Friday). **Spread** = median of the bar
  spreads of the last 60 cached FTMO days (`data/cache/mt5`), no per-time spread; **slippage** = half the spread (rough, like the others).
  **Commission is not in `symbol_info`**: FX majors / crosses **$5**, XAGUSD **$6** are assumptions (as GBPUSD / XAUUSD), indices, energy,
  DXY, NATGAS **0**, all to be confirmed by the user. XAGUSD's $6, BTCUSD / ETHUSD's 0 and their swap 0 were replaced on 2026-10-15
  by the percentage model of *Real fees* below.

  | Symbol | Spread | Contract | Quote to USD | Swap long / short | Triple |
  |---|---|---|---|---|---|
  | EURUSD / AUDUSD / NZDUSD | 0.00002 / 0.00002 / 0.00003 | 100,000 | 1 | -8.53 / +0.21, -3.04 / -6.54, -4.78 / +0.01 | Wed |
  | EURGBP | 0.00004 | 100,000 | 1.3271 | -8.4804 / 0 | Wed |
  | USDJPY / EURJPY | 0.003 / 0.009 | 100,000 | 0.00632 | +1.0813 / -11.0347, +1.328 / -7.6199 | Wed |
  | USDCAD / USDCHF | 0.00003 / 0.00005 | 100,000 | 0.7047 / 1.2088 | +0.4792 / -8.4426, +1.5715 / -16.2468 | Wed |
  | XAGUSD | 0.049 | 5,000 | 1 | -68.05 / +0.30 | Wed |
  | GER40 / EU50 | 1.53 / 1.06 | 1 | 1.1211 | -5.0571 / -0.0511, -1.2359 / -0.0124 | Fri |
  | UK100 | 1.45 | 1 | 1.3271 | -3.2063 / +0.148 | Fri |
  | JP225 | 10.0 | 10 | 0.00632 | -0.5683 / -0.1894 | Fri |
  | US30 / US2000 | 2.28 / 0.93 | 1 | 1 | -11.7596 / +0.5936, -0.5735 / -0.0172 | Fri |
  | USOIL / UKOIL | 0.075 / 0.069 | 100 | 1 | +4.966 / -22.54, +6.097 / -27.582 | Fri |
  | NATGAS | 0.06 | 1,000 | 1 | -5.84 / +1.27 | Fri |
  | DXY | 0.018 | 100 | 1 | -2.337 / +0.118 | Fri |
  | BTCUSD / ETHUSD | 1.0 / 0.6 | 1 / 10 | 1 | percentage, -30 % per year, both sides (see *Real fees*) | Fri |

- **Real fees: FTMO and Binance** (rule set by the user, 2026-10-15: "integrate FTMO's real fees and Binance's fees for crypto and show
  them"). Commission and swap can now also be a **percentage of the notional**, and Binance funding is a third cost. Everything is in R,
  net only (gross = chart prices); lots and contract size cancel, so only prices and the SL distance matter:

  commission_R = `commission_pct_per_side` x (entry fill + sum(share x exit fill)) / SL distance (+ the fixed USD part as before)
  swap_R = nights x `swap_*_pct_year` / 365 x entry / SL distance (+ the USD part as before; triple day as before)
  funding_R = - sign x sum(share x sum of the funding rates with entry < timestamp <= exit of that part) x entry / SL distance
  (sign +1 long, -1 short: longs pay a positive rate, shorts receive it; notional approximated at the entry price)

  **B6 (rule set by the user, 2026-10-22):** entry commission uses the actual fill price,
  including spread and adverse entry slippage; each exit uses its own fill price.

  | Symbol group | Commission | Swap | Funding |
  |---|---|---|---|
  | FX (GBPUSD, GBPJPY, EUR/AUD/NZD/USD crosses) | $5 per 1.0 lot round turn ($2.50 per side), unchanged | USD per lot, unchanged | no |
  | **XAUUSD, XAGUSD** | **0.0014 % of notional round turn** (0.0007 % per side). Was $6 per lot for both until 2026-10-15. | USD per lot, unchanged | no |
  | Indices, energy, DXY, NATGAS | none, unchanged | USD per lot, unchanged | no |
  | **BTCUSD, ETHUSD (FTMO)** | **0.065 % round turn (0.0325 % per side)** | **-30 % per year of notional per night, long and short** (MT5 percentage mode; was 0) | no |
  | **BTCUSDT, ETHUSDT (Binance USD-M)** | **taker 0.05 % per side** (a market fill is a taker; maker would be 0.02 %). Replaces the old fixed-price placeholder. | none | **every 8 h from `data/cache/binance_funding/<SYM>.csv`**, applied at each timestamp a position is open; spread 0 |

  Example, SL distance 1 ATR (numbers are illustrative, long, entry = exit price, round trip, no swap night): XAUUSD at 3,000 with ATR 15:
  0.000007 x 6,000 / 15 = **0.0028 R**. BTCUSD at 100,000 with ATR 1,500: 0.000325 x 200,000 / 1,500 = **0.043 R** (+ 0.3 / 365 x 100,000 / 1,500 =
  0.055 R per night held). BTCUSDT at 100,000 with ATR 1,500: 0.0005 x 200,000 / 1,500 = **0.067 R** (+ funding: a typical 0.01 % per 8 h = 3 x 0.0001 x
  100,000 / 1,500 = 0.02 R per day long).
  **To be confirmed with the first demo trade's deal history** (FTMO values only; the numbers come from third-party sources that agree, FTMO's own
  page did not load). Sources, read 2026-10-15: https://ctrader.com/prop-firms/ftmo, https://propvator.com/blog/ftmo-trading-conditions/ (FTMO),
  https://www.binance.com/en/support/articles/360033544231 (Binance USD-M fee schedule, regular user). The crypto swap sign / value per symbol is
  read from the terminal's `symbol_info` (`swap_mode`, `swap_long`, `swap_short`) and set when checked. Funding uses the entry price as notional (not the
  mark price at the timestamp); a funding symbol without its CSV raises an error instead of silently using 0. Shown: `commission_r`, `swap_r` and
  `funding_r` per trade in `trades.csv` (all inside `r_net`), and the results page's performance summary has the rows spread / commission / swap /
  funding (R, negative = cost). `CostConfig.funding_enabled` switches funding off; the percentage fees follow `commission_enabled` and `swap_enabled`.
- ⚙️ **Cost filter** (user, 2026-10-14: build it in the engine, off by default; details chosen by Claude; knowledge base
  I-45 cost-to-target): `CostConfig.max_cost_r`, default **0 = off**. An order whose spread + commission in R at its fill
  (spread / SL distance + commission as a price distance / SL distance; only the costs that are switched on; no swap, no
  slippage) is **above** this value is not filled. The engine tells the strategy (`Strategy.on_order_skipped(ref, now)`,
  default: nothing): strategy 2 counts no trade for it and keeps the setup open for a later entry; strategy 4 stays flat
  and the next signal event tries again. Equal to the limit is filled. Strategies 1 and 3 have no hook yet: for their
  per-session limits a skipped order counts as taken (both are paused / dropped). The filter studied on strategy 2's
  trades: ROADMAP 10.5.
  Percentage commission is estimated with both sides at the actual entry fill, while spread scaling uses the chart entry
  (B6; rule set by the user, 2026-10-22). Slippage is not added as a separate filter cost.
- ⚙️ **Slippage** (B4; rule set by the user, 2026-10-22): `SymbolCosts.slippage` in price units per fill, always
  against the trader on **market entries, stop fills (including gap stops), and time / signal / end-of-data exits**.
  Never on limit entries or TP fills. Scale at the chart entry price like the fixed spread and reuse that amount at exits.
  Spread/commission switches do not disable slippage; a zero symbol setting does. Defaults (rough starting estimates, to be checked against FTMO demo fills):

  | Symbol | Slippage per fill |
  |---|---|
  | NAS100 | 1.0 point |
  | US500 | 0.25 point |
  | XAUUSD | 0.10 |
  | GBPUSD | 0.2 pip |
  | GBPJPY | 0.3 pip |

- **Break-even including costs** (B5/B6; rule set by the user, 2026-10-22): solve the remaining portion's net result
  for exactly zero using actual entry fill, adverse stop slippage, spread, and commission at the exit fill.
  For sign `s`, entry fill `E`, fixed round-turn commission in price units `F`, per-side rate `p`, solve
  `s * (X - E) = F + p * (E + X)` for exit fill `X`; the chart stop is `X - short_spread + s * slippage`.
  This excludes swap/funding and previously realised TP profits; stop gaps can still lose money.
  After TP1, move the stop only if BE is strictly behind TP1 (long BE < TP1, short BE > TP1).
  At equality or beyond TP1 the original SL stays.

### Daily & account protection
- ⚙️ **Personal daily stop:** **−2%** of the balance at the start of the day. Counts **closed trades plus floating P/L** (rule set by the user). When reached: no new entries for the rest of the day; open trades keep running with their SL/TP. Day = midnight to midnight `Europe/Prague` (CE(S)T), like FTMO. (The earlier "or 2 losses" rule is dropped.)
- ⚙️ **Max total open risk:** **2%** of the balance. A new trade is skipped (logged) if it would push the open risk above it.
  - A trade counts at its **full risk as long as its SL can still be hit**, and as **zero risk once the SL is at break-even** (rule set by the user). Being close to a TP changes nothing.
  - ⚙️ **Correlation groups:** symbols in one group share the limit like one symbol. Default: **GBPJPY + GBPUSD on**, **NAS100 + US500 off** (traded independently, rule set by the user).
- ⚙️ **Drawdown scaling:** when the equity falls **4%** below its highest point so far, the risk per trade is **halved** (⚙️ factor 0.5). Back to normal as soon as the equity is **less than 4% below the high again** (rule set by the user). Example: peak 104,000 → at 99,840 (−4%) risk 1% → 0.5%; back to 1% above 99,840.
- Near-target scaling: dropped for now; it belongs to the prop-firm field (› Later).

### Account simulator (`risk/account_sim.py`)
- Replays the trades in time order, candle by candle, without lookahead.
- Tracks balance and **equity including floating P/L**, using the worst point of each candle.
- Applies sizing, costs, the daily stop, max open risk and drawdown scaling; skipped trades are listed with their reason.
- Handles trades that stay open past midnight (their floating P/L counts toward the new day).
- **Output:** equity and balance curve, final balance, return %, max drawdown (% and $), longest drawdown, win rate, expectancy, profit factor, number of trades taken / skipped, worst day, results per month.

### Monte Carlo (`risk/monte_carlo.py`)
Kept in the base backtest (rule set by the user).
- Samples **whole trading days** ⚙️ **1,000** times and simulates the account for each order with the same settings (sampling rules below).
- **Output:** distribution of max drawdown and final balance, e.g. "in 95% of the runs the max drawdown stays below X%", a fan of simulated equity curves. Main use: choosing a safe risk %.

### Monte Carlo report (ROADMAP 12.7; rules set by the user, 2026-10-15)

#### Skill vs trend, and bounds (V2.4d 7 + 8)

The report and `skill_bounds.json` show raw and detrended net/mean R by symbol and
total, long/short/flat time shares and the no-skill benchmark, BCa and t-based
90/95% lower bounds of daily MTM and trade means, and daily log PF with BCa bounds.
Use `research-runner.md` > Skill vs trend, and bounds for formulas, defaults,
position conventions and unavailable cases. Compute from the run's own period,
trades and SymbolSources, with saved daily MTM preferred. Set `skill_is_trend`
when positive raw R becomes nonpositive detrended R; leave the verdict unchanged.

One HTML report per backtest run (`python -m backtester.tools.monte_carlo <run-id>` ->
`results/<run-id>/monte_carlo/report.html`), built from the run's trade list (R). All four kinds of Monte Carlo
(`knowledge/topics/backtest-frameworks.md`), every random draw seeded (⚙️ seed **42**). It ends every test with a
clear verdict.

#### Matched monkeys (V2.4c T-14, accepted 2026-10-23)

For every strategy, compare its actual trade list with three seeded null models on the
same symbols' M1 data. Preserve trade count and long count exactly per symbol in every run.

1. Random entries: uniformly sample M1 closes with replacement from `_window_candidates`
   (observed New York weekdays and 15-minute time buckets within the entry date range).
   Permute the real (initial stop distance, elapsed hold seconds) pairs onto those entries.
2. Random exits: keep real entries and stops; independently permute real elapsed holds.
3. Both random: sample entries as in 1; independently permute stops and holds.

All permutations are per symbol (Opus clarification, 2026-10-23). Direction slots retain the
real long/short counts; stop distance is mirrored around the sampled bid close. No target.
Use entry-screen exit replay and costs, including stop gaps at the open, slippage, spread,
commission and swap. Only candles opening at or after the entry close can resolve an exit.
Holds use the last M1 close by the deadline, at least the first subsequent candle, and are
clipped to available data as in entry screening. Exclude final candle closes from random
candidates because they have no subsequent exit candle. Reject invalid trades or missing
symbol data explicitly; empty lists are unavailable, never passing.

Defaults: 1,000 runs, seed 42 (8,000 is configurable); runner: 200 development runs on the
chosen variant only, skipped by grid `monkeys = false`. Report total net R and max drawdown
in additive R, ordered by exit time (stable input order for simultaneous exits), including
the initial zero equity peak. Each statistic reports median, 5th and 95th percentiles and
the real result's percentile (half credit for ties within 1e-12). Lower DD is better.
Each kind passes iff both favorable percentiles are >= 90; any failure flags `monkey_beaten`.
This diagnostic does not alter selection, DSR, trial counts or golden lists. Standalone
tool logs one source backtest per variant, not the synthetic runs; refuses test dates
without `--allow-test-period`, writes `summary.json` and `report.md` under
`results/monkeys/<strategy>_<time>/`, and supports sequential `--workers 1`.

Monte Carlo verdict check 2 keeps its existing >= 95 threshold: gap fade uses kind B where
available; other strategies use matched-monkey kind 1 net-R percentile. Missing data must
be reported as unavailable, never replaced by a different period's percentile.

#### Report and verdict

- **Verdict** (first thing in the report): **EDGE** when all seven checks pass, **WEAK** when one or two fail,
  **NO EDGE** otherwise:
  1. mean net R per trade > 0 with t = mean / (sd / sqrt(n)) ≥ ⚙️ **2**;
  2. net R above ⚙️ **95 %** of random-entry runs (gap fade kind B where available,
     matched-monkey kind 1 for all other strategies; see Matched monkeys);
  3. both halves of the run's own period (split at the middle date of start..end; rule set by the user,
     2026-10-15) net positive;
  4. net R positive with costs x ⚙️ **1.5** (`RobustnessConfig.cost_stress`);
  5. net R positive without the best trade;
  6. median net R of the random-fill runs (kind C) > 0.
  Details (`analytics/verdict.py`; n/a rule confirmed by the user 2026-10-15): a check without
  input (e.g. random entries for a strategy without a baseline yet) is n/a, listed and named in the reason, and
  counts neither as pass nor fail; t ≥ 2 and percentile ≥ 95 pass at equality, the net checks need > 0; the
  random-path warning (kind D) is raised when a symbol's mean net R per trade on the random paths is above 0, a
  banner only, not part of the verdict.
  7. **Deflated Sharpe** DSR ≥ ⚙️ **0.95** (7th check, rule set by the user 2026-10-16; see › Trial log and
     deflated Sharpe). With seven checks, WEAK still means one or two failed.
- **A. Day sampling** (V2.4d item 4, accepted 2026-10-23): ⚙️ **1,000** runs.
  `MonteCarloConfig.sampling="block_bootstrap"` is the default: stationary bootstrap
  (Politis–Romano), starting uniformly at a historic day, continuing to the next day modulo
  the history length with probability `1 - 1/block_days`, otherwise restarting uniformly.
  Block lengths are geometric, mean `block_days` (default **5**, finite and >= 1).
  Every path has the historic number of days; replacement permits repeats and omissions.
  `sampling="permutation"` retains the exact historic seeded permutations for comparison.
  The same orders feed account statistics, drawdown duration, fan, FTMO challenges/funded
  phase, adaptive risk, prop cards and risk sweeps. Reports name sampling and block length.
  A "day" = a weekday of the run's period
  (midnight to midnight `Europe/Prague`; days without trades included, so days and months are real calendar
  lengths); trades belong to their exit day and keep their order and times inside it. Account per run: start
  ⚙️ **100,000 USD**, risk ⚙️ **0.5 / 1 / 1.5 %** of the current balance per trade, shown **side by side**
  (user: try different risks side by side); P/L = r_net x risk $. Simplification until the account simulator
  (5.2): no lot rounding, no personal daily stop, max open risk or drawdown scaling.
  - **Fan chart** (like a stock-price Monte Carlo chart, user 2026-10-15): the balance of ⚙️ **20** highlighted
    runs over the days, the 5 / 50 / 95 % bands of all runs behind them, best and worst end marked, the real
    order as a bold line.
  - **Numbers** per risk: final balance and gain on 100k (5 / 50 / 95 %), average gain per month in % (mean and
    median; a month = ⚙️ **21** trading days), share of profitable months, max drawdown (median and 95 %),
    P(max drawdown > 10 %), longest drawdown in days, worst day, longest losing streak, profit factor, win
    rate, expectancy, trades per month.
- **Double-bootstrap drawdown bounds** (`risk/drawdown_bounds.py`, Masters ch.6): separate
  additive daily-R calculation, independent of the compounded account replay. Use the run's
  complete `daily.csv` MTM column when present (V2.4d 1+2), otherwise exit-booked daily R;
  label the source. Reject malformed/nonfinite daily data rather than silently falling back.
  Outer **200** stationary-bootstrap histories of the original length; per outer history,
  inner **1,000** stationary-bootstrap future paths of **126** days. Both use mean block
  length **5**, seeded **42**, configurable in a frozen config. Include the initial zero
  equity peak: max drawdown R = max(running peak of cumulative R minus cumulative R).
  For q = **0.50 / 0.90 / 0.95 / 0.99**, take each outer history's inner q-quantile;
  report its outer median and one-sided **90 % / 95 %** upper bounds (numpy linear
  quantiles). Table in R and percent balance at each configured risk: `R * risk * 100`,
  fixed fraction without compounding. Empty input is explicitly unavailable; a nonnegative
  series gives zero. These are estimates for the stated future horizon, not guarantees.
  Monte Carlo HTML + JSON include the table. Research writes `drawdown_bounds.json` beside
  the chosen development run and each completed test run, with blocks in `report.md`;
  no test is triggered solely to calculate bounds. Defaults must run well under one minute.
- **FTMO 2-Step** on each reshuffled run (rules in › Prop-firm field): Phase 1 +10 %, Phase 2 +5 %, daily loss
  5 % and max loss 10 % (static) of the initial balance, at least 4 trading days (days with a trade). Attempts
  follow each other along the run (a new attempt starts the day after the last one ended, fresh balance).
  **Daily-loss base** (rule set by the user, 2026-10-22): daily loss = balance at FTMO midnight
  Europe/Prague minus current equity; the limit = `daily_loss` x initial balance, regardless of the
  day-start balance. The live guard uses `ftmo_daily_loss_percent / 100` for this fraction.
  **Daily loss approximation** (user, 2026-10-15): the R list has no floating P/L, so a trade still open counts
  as if at its stop: the day's worst point is checked at every entry and exit of the day as closed P/L of the
  day so far minus, for each open trade, the risk x max(1, -r_net). Conservative (pass rate a bit too low).
  Adaptive replay instead reserves only each open trade's initial risk money; its eventual R is applied
  only at its exit (rule set by the user, 2026-10-22; see Adaptive risk below).
  Output per risk: pass probability (both phases), fails split daily / max loss, median days to pass,
  P(funded account lost within ⚙️ **126** trading days).
  **Funded account** (rule set by the user, 2026-10-20): risk per trade = risk x the **initial** balance (not the
  current one), and the profits are paid out at each day end (the balance goes back to at most the initial one), so
  profits neither raise the risk nor buffer the 5 % / 10 % limits. The challenge phases keep risk x the current balance.
  Implementation details (chosen by Claude 2026-10-15, `risk/monte_carlo.py`): max drawdown on the closed balance
  after every trade, fan / worst day / months on day-end balances; only full 21-day months; a trade exiting on a
  weekend moves to the next weekday; reaching a limit counts as a breach, daily loss checked before max loss;
  **Passing days and unfinished attempts** (rule set by the user, 2026-10-22): a phase passes only
  after the whole day is played without a breach, with the target reached on its closing balance and
  >= 4 trade days. Later trades that day can lose the target or breach a limit. Each phase and the funded
  account start fresh, a new attempt starts the next day. At the data end, an attempt still in either
  challenge phase is unfinished and reported separately as a count and share of all attempts. No attempt
  starts without a remaining trading day. `attempts` retains the finished count; `unfinished_attempts`
  is the unfinished count; `total_attempts` is their sum; `unfinished_share` is unfinished / total
  (0 when there are no attempts). Pass probability = passes / finished attempts (0 when none finish;
  the UI shows "—"), with unfinished share displayed alongside it, for fixed and adaptive risk.
  The full Monte Carlo HTML report and adaptive-risk sweep (JSON, CSV, Markdown) also retain
  unfinished count and share (rule set by the user, 2026-10-22).
  The funded loss rate counts only accounts lost or watched the full 126 days. **Known gap:** a trade open across
  midnight Prague counts only from the start of its exit day, not on its entry day (daily loss slightly
  undercounted for overnight trades; none for the gap fade).
  **Post-ruin statistics:** a daily or full-month block starting with a non-positive balance has
  return 0%; the block that first falls from a positive balance to zero returns -100%. Ruin is
  absorbing in the compounded path, so later blocks contribute zero rather than undefined returns.
- **B. Random entries** (12.1): ⚙️ 1,000 runs. Gap fade: the same gap days with the same stop and exit, a coin
  flip per day between fading and following the gap (follow = the fade trade mirrored: same distances, the
  other direction). Other strategies: random entry times inside the strategy's own window with its own stop and
  exit (built when a strategy needs it). Random baseline on non-gap days: dropped (user, 2026-10-15). Output:
  percentile of the strategy's net R, mean and 5 / 95 % of the random runs.
- **C. Random fills** (12.6; B4, rule set by the user, 2026-10-22): ⚙️ 1,000 runs; each market fill
  (entry, stop / time / signal / end-of-data exit) gets an extra slippage drawn
  uniform from 0 to ⚙️ **2** x the symbol's slippage setting, in R of the trade's stop distance. Output: net R
  5 / 50 / 95 %. Each market exit part gets its own draw, weighted by its share; TP parts get no exit draw.
  Limit entries receive no entry draw. `limit_fill` is preserved in trade results and `trades.csv`;
  historical CSVs without this field retain the market-entry assumption.
- **D. Random price paths**: ⚙️ **20** seeded random-walk M1 paths per symbol with the symbol's real volatility
  per hour of day, ⚙️ **2** years each, run through the same strategy and costs. Expected: net R per trade about
  minus the mean cost; clearly more is reported as a warning (bug or lookahead), not as an edge.

### Trial log and deflated Sharpe (ROADMAP 12.10; rules set by the user, 2026-10-16)
Why: picking the best of many variants finds a "winner" even on pure noise (López de Prado, *AFML* 11, 14.7;
`knowledge/topics/statistics-and-bayes.md`). Every tried variant is logged, and the verdict deflates the chosen
one's Sharpe by the number of trials.

- **Trial log:** `results/trials.jsonl` (git-ignored like all results), one JSON line per backtest of a variant:
  family, strategy, the variant's settings, symbols, start, end, data source, time written, trade count, net R,
  mean / sd / skewness / kurtosis of net R per trade, Sharpe per trade. Written by `run.py`, the Monte Carlo
  tool (also with `--run`, i.e. the results page's Full Monte Carlo button) and `tools/gap_fade_grid.py` (one line per variant; other tools later). Append-only; a line with the same
  family, strategy, settings, symbols, period and source as an earlier one replaces it when read (rerunning a
  variant is not a new trial).
- **Family** = the set of variants the chosen one was picked from. ⚙️ Default: the strategy name; `--family`
  overrides it in every writing tool.
- **Back-fill** (user, 2026-10-16): trials run before the log existed are added by hand
  (`python -m backtester.tools.trials add ...`), with their numbers where the old result files have them,
  otherwise as count-only lines (count for N, no Sharpe).
- **Marked-to-market daily series (V2.4d items 1?2):** additive daily net R and signed
  position; existing daily statistics and DSR stay on exit-booked daily net R.
  Calendar days end at the following Europe/Prague midnight. Weekend contributions move
  to the next weekday; out-of-period contributions clamp to the first/last weekday.
  At cuts before exit use the last M1 bid close whose close time is <= cut, adding the
  trade's spread for shorts. Value remaining shares from actual entry fill; realized
  partial fills remain in cumulative value. Differences form daily R and final exit settles
  to saved r_net, conserving each trade's total within 1e-9. An exit exactly at midnight
  settles on its new calendar day's exit booking; the preceding cut uses the bid mark,
  leaving exit costs to the exit day. Parts exiting exactly at a cut are marked there
  before their fill is realized in the following day.
  Spread/slippage included in fills are never deducted twice. Book the whole commission_r
  on entry day for every commission model, including old runs, without cost settings.
  Saved swap/funding totals have no recoverable charge schedule: spread each evenly across
  Prague midnight cuts strictly after entry and <= exit (no cuts: exit day), on the day
  ending at that cut. Position is signed remaining share integrated over actual calendar
  day duration in UTC (DST included), counting only time on the named weekday inside
  the requested period. Weekend/out-of-period holding time is omitted from position,
  rather than added to another weekday; only R contributions follow the mapping above.
  Missing marks or invalid/nonfinite prices and stop distances raise errors.
  Read M1 through SymbolSources once per symbol/consecutive cached-day block.
  TrialRecord.series optionally links daily.csv relative to results/; old lines default
  to None. read_series defaults to net_r_exit_booked and also accepts net_r_mtm or position.
  series_matrix aligns the date union with zero padding in input record order; records
  without series yield empty arrays and an all-zero matrix column.
- **Daily Sharpe** (rule changed by the user 2026-10-20, ROADMAP 12.13; before: per trade): SR = mean / sd (sample sd)
  of the **daily net R** of the run, not annualised; a day = a weekday of the run's period, midnight to midnight
  `Europe/Prague`, trades by exit day, days without trades = 0 (as Monte Carlo kind A); n = number of days; skewness g3
  and kurtosis g4 (not excess, normal = 3) of the daily net R. Why: per-trade Sharpes of runs with very different trade
  counts are not comparable (12.9: 302 vs 1,858 trades), daily ones are, also for a weighted portfolio. Trial-log lines
  store the daily statistics too (days, daily mean / sd / skew / kurtosis / Sharpe); lines without them (written before
  2026-10-20) count for N but not for V.
- **PSR(SR\*)** = Φ( (SR − SR\*) √(n − 1) / √(1 − g3·SR + (g4 − 1)/4 · SR²) ); shown as PSR(0).
- **DSR** = PSR(SR0) with SR0 = √V · ((1 − γ) Φ⁻¹(1 − 1/N) + γ Φ⁻¹(1 − 1/(N·e))), γ = 0.5772 (Euler's constant),
  N = number of trials in the family (count-only lines included, at least 1; N = 1 gives SR0 = 0, DSR = PSR(0)),
  V = sample variance of the daily Sharpes of the family's lines that have one, when there are ⚙️ **2** or more;
  otherwise V = 1/n of the evaluated run (n = days; the variance of a zero-skill Sharpe estimate; chosen by Claude 2026-10-16).
- **Check 7** of the verdict passes at DSR ≥ 0.95; n/a with fewer than 2 days, zero sd or a non-positive
  denominator under the square root. Same rule in the Monte Carlo report and the portfolio tool (on the combined,
  weighted daily R).
- The report shows PSR(0), DSR, N, V, SR0 and the family name.

#### Effective sample counts (V2.4d item 5 / T-19)

Research significance reports effective variant N beside the actual N, using aligned
development marked-to-market daily correlations: max(1, N / (1 + (N - 1) * mean
pairwise correlation)). It also reports the chosen variant's average trade uniqueness
and sum of uniqueness weights from daily concurrent trade intervals. Exact conventions
and unavailable cases: research-runner.md > Significance of the best variant.
These are diagnostics only: the trial log, DSR's actual N and variance, t-statistics,
selection and existing daily statistics remain unchanged. Substituting effective N
into DSR requires a later user decision.

### Entry screening (ROADMAP 12.12, idea T-13; rules set by the user, 2026-10-20)
Why: most ideas die at the entry (Davey, *Building Winning Algorithmic Trading Systems* ch.12). The battery asks whether a
strategy's entries carry information at all, independent of its exit, before a full strategy is tuned.

- **Input:** the trades of a backtest (entry time, direction, entry price, initial stop distance = 1R, symbol, signal
  timeframe). The strategy's own exit is replaced by the test exits below, re-simulated on the **M1** candles with the
  engine's rules: costs from the cost model (spread, commission, swap at the 17:00 New York rollover, adverse market-fill
  slippage per B4), SL and TP inside one candle -> SL first, no lookahead.
- **Test exits:**
  (a) **N bars:** exit at the close of the N-th bar of the signal timeframe after the entry, ⚙️ N = **1, 2, 3, 5, 10, 20**;
  the strategy's own stop stays active (user, 2026-10-20);
  (b) **1R / 1R:** stop and target both one R from the entry (a no-edge entry wins about 50 % before costs);
  (c) **random time:** exit at a random time drawn so the mean hold equals the strategy's mean hold, ⚙️ **1,000** seeded
  runs (seed **42**), the strategy's own stop active; reported as the median and the strategy's percentile;
  (d) **reversed signal:** the opposite direction with the mirrored stop, costs paid again (each test exit);
  (e) **hit-rate scan:** share of entries whose price is above (long) / below (short) the entry x bars later, x = the N
  set, against the same scan on ⚙️ **1,000** shuffled entry times inside the strategy's own trading windows.
- Positions that cross the 17:00 New York rollover pay the real swap (user, 2026-10-20).
- **Pass** (all three): mean net R > 0 in ⚙️ **≥ 70 %** of the cells (N set x the variants screened); the 1R / 1R win
  rate ⚙️ **≥ 52 %**; and the real entries beat the random-time exit (c) (above its ⚙️ **90th** percentile, confirmed by the user 2026-10-20) on net R.
- Every screened variant is logged in the trial log (family `screen_<strategy>`).
- **Output:** `results/entry_screen/<strategy>/` with a per-cell CSV (N, variant, trades, win rate, mean gross / net R,
  long / short split, halves at the middle of the period), the summary with PASS / FAIL and the reasons.
- **Implementation choices where the rules above are silent** (built 2026-10-20, `analytics/entry_screen.py`; open to
  the user's correction): "N bars later" = the last M1 candle that closed by entry + N x bar minutes, never before the
  first candle after the entry (data gaps / weekends end the hold at the last candle before the gap); random exit =
  hold drawn uniform on [0, 2 x mean hold] per trade and run (mean hold in expectation; the sample mean is reported),
  the "strategy's percentile" is that of its own total net R among the 1,000 random totals (ties count half); 1R/1R
  stop = the trade's initial stop distance, target the same distance, win rate = target hits / (target + stop hits),
  trades unresolved at the end of the data left out; reversed signal = opposite direction, stop mirrored at the same
  distance, spread / commission / swap of the new direction; shuffled entry times: per symbol a uniformly drawn M1
  candle close on the New York weekdays and 15-minute time-of-day buckets in which the strategy entered, within its
  entry date range, with the direction of the real trade it replaces (ties count as misses on both sides); across
  several variants the cells and the bracket results are pooled and the percentile is the median. The hit-rate scan is
  reported (z against the shuffled runs) but is not part of the pass rule.
- **First use (user, 2026-10-20):** re-audit strategies 1-7 with their default settings on their own symbols, development
  period only (before 2021-09-14).

### Portfolio tool (ROADMAP 12.9; rules set by the user, 2026-10-20)
Why: combine weak, uncorrelated edges into one account without fooling ourselves (Carver, Davey, López de Prado;
`knowledge/topics/combining-edges.md`).

- **Components:** a list (strategy, settings, symbols, period, data source); the tool runs each backtest and takes its
  trade list in R. All components share one period.
- **Daily R:** each component's net R per FTMO day (midnight `Europe/Prague`, trades by exit day, as Monte Carlo kind A).
  **Correlation** of the daily R between components over the whole period and in rolling ⚙️ **126**-trading-day windows
  (about 6 months; min / median / max per pair).
  Empty or constant daily series have zero correlation with other components and diagonal 1.
  Empty rolling windows are omitted. The usual IDM formula still applies; for N empty components
  it gives sqrt(N), subject to the same cap.
- **Weights:** ⚙️ **equal risk** per component (weight 1 / number of components; never optimised, user 2026-10-20). Each
  trade's R is multiplied by its component's weight, so the account risk per trade is the Monte Carlo risk x weight.
  **IDM** = 1 / sqrt(w' H w) with H the whole-period daily correlation (negative values floored at 0, ⚙️ cap **2.5**)
  is shown; ⚙️ `apply_idm` off by default (it raises the risk, user 2026-10-20).
- **Report:** the Monte Carlo report on the combined, weighted trade list (fan chart, numbers, FTMO pass probability) and
  the 7-check verdict: halves at the middle of the period; random entries (kind B) and random fills (kind C) per
  component where the strategy supports them, combined with the same weights, otherwise n/a; DSR with **N = the sum of
  the trials logged in all component families** and V from all their Sharpes. Plus the correlation table, each
  component's own numbers next to the combination, and the IDM.
- **First use (user, 2026-10-20):** ORB band 0.25 ATR, no target, min_rel_volume 1.5 on US30 / US2000 / NAS100 / US500;
  gold gap momentum (`fx`, entry_z 0.1, stop_atr 0.5, exit 11:00); gap fade defaults on NAS100 / US500; FTMO MT5 data
  2021-09-14..today. This period was used by the ORB and gold tests: the result is a sanity check, not a fresh test.

### Risk sweep (`risk/sweep.py`)
- A grid over the settings to compare results (max drawdown, return, Monte Carlo 95% drawdown).
- Sweepable: risk per trade (e.g. 0.25–1.5%), daily stop (1–3%), **max open risk** (rule set by the user), drawdown-scaling threshold and factor.

## UI page: "Risk" (Dash)
- **Left panel:** trade source (a strategy backtest run or the imported manual R log), starting balance, risk per trade, costs per symbol, daily stop, max open risk + correlation groups, drawdown scaling, Monte Carlo runs.
- **Main panel:**
  - equity curve with drawdown below it
  - key numbers (› Account simulator output) and skipped trades with reasons
  - Monte Carlo fan of equity curves and drawdown distribution
  - sweep heatmap (e.g. risk % × daily stop)

## Prop-firm field (later)
An extra field in the backtest, added later (rule set by the user): simulates FTMO challenge phases and funded accounts on the same trades and estimates the probability of passing.
- **Phases:** Phase 1 → Phase 2 → funded, result per phase, pass/fail with reason and day.
- **Limits:** marks where the FTMO daily loss or max loss would have been broken (rule set by the user: this belongs here, not in the base backtest).
- **Pass probability** via the Monte Carlo runs: pass rate, fail rate (daily vs. max loss), median days to pass.
- **Near-target scaling** (reduce risk close to the profit target): to be defined then.
- **Adaptive risk** (rules set by the user, 2026-10-20; ROADMAP 5.7): in a challenge phase and in the funded
  account the risk per trade shrinks as the account gets closer to the max-loss line, so an unlucky start does not
  easily end the attempt (passing may take longer).
  - **Room** = equity at the entry minus the max-loss line (initial balance x (1 - 10 %), static, FTMO); **full
    room** = 10 % of the initial balance.
  - **Risk** = base risk x (room / full room), **linear**, never above the base risk (an account in profit trades the
    base), never below ⚙️ **floor** x base risk (default **0.25**). It follows the equity both ways (wins restore it).
    Base risk in the challenge = a % of the current balance as before; in the funded account a % of the initial
    balance (12.14); the factor applies on top.
  - **Daily risk budget** ⚙️ **3 %** of the initial balance (rule (a), user 2026-10-20): a new trade's risk is cut
    so that today's loss so far + the initial risk money of every open trade +
    the new trade's risk stays ≤ 3 %; if not even the floor risk fits, the trade is skipped. With stops holding a day
    cannot lose more than 3 %, so the 5 % daily limit is out of reach. Losses beyond the stop can still breach
    at the exit; they cannot be anticipated at entry (rule set by the user, 2026-10-22).
  - Same limits in the challenge and the funded account (FTMO 2-Step: 5 % daily, 10 % static max loss).
  - **Shown:** the prop-firm card has, per base risk, a line "fixed" and a line "adaptive" (pass probability, fails
    daily / max, average and median days to pass, funded lost, and for adaptive the share of trades the budget skipped).
  - **Modelling choices of the simulation** (`risk/adaptive.py`, `monte_carlo._play_day_adaptive`; Claude 2026-10-20,
    to be confirmed): (1) the equity at the entry is the *closed balance* then (the R list has no floating P/L); (2)
    the risk $ of a trade is fixed at its entry (factor x base) and its exit P/L = r x that risk $; exits are matched
    to entries by a trade id on the day's events; (3) "today's loss so far" = day start balance minus closed
    balance, not below 0; (4) every entry decision and the open-risk loss approximation use only the initial
    risk money fixed at each open trade's entry, never its later result (rule set by the user, 2026-10-22).
    This includes portfolio weights: the weighted initial risk is reserved once; weighted R is converted
    back to the trade's R only on exit. The new trade also counts at 1 x its initial risk money;
    (5) a skipped trade's R is not taken and
    the day still counts as a trading day; (6) a trade open from an earlier day is entered at the day start with the
    risk of that moment. Fixed and adaptive paths both apply the day-end pass rule above.
  - **Variant sweep** (user, 2026-10-20: "we need to backtest all these variants"): base risk, floor and daily budget
    are swept on the trades of **every strategy**; best variant chosen on the development years (before the
    2021-09-14 cut-off), checked once on the later MT5 period and across strategies; the defaults above stay until
    the user picks from the results.
- **Where it shows** (decided by the user, 2026-10-20): no separate section; a "Prop firm" card on every
  backtest's results page (pass probability, fails daily / max loss, median days to pass, funded account lost,
  at 0.5 / 1 / 1.5 % risk, from the day-reshuffle Monte Carlo, FTMO 2-Step first) and a "Full Monte Carlo"
  button there that runs the whole report (ROADMAP 12.7) in the background; other firms' presets later (5.6).
  **Built 2026-10-20 (to be checked by the user):**
  - *Card* (`risk/prop_card.py`, `ui/prop_firm_card.py`): the run's R trades (trades.csv, all symbols as one account) go
    through kind A (day reshuffle, ⚙️ 1,000 runs, seed 42) and the FTMO 2-Step simulation at 0.5 / 1 / 1.5 % risk
    (the `MonteCarloConfig` defaults). Rows: pass probability (both phases, passes / finished attempts),
    unfinished share of all attempts (rule set by the user, 2026-10-22), failed daily loss / max loss (share of all
    attempts), median days to pass, funded account lost within 126 days; "—" for pass probability where no attempt
    finished, while unfinished share is still shown. Below the
    table one line says how it is estimated (reshuffled trading days; open trades count as at their stop, so the
    daily-loss check is conservative). **Too little data** (⚙️ `PropCardConfig`: fewer than **100** trades or fewer than
    **120** weekdays in the run's period; limits accepted by the user 2026-10-20) shows the reason instead
    of numbers. The firm is a dropdown over `FIRMS` (FTMO 2-Step only for now; another firm's rules are one more preset).
  - *Speed and cache:* a run of 9,000 trades takes about 20 s, one of 17,700 trades about 40 s, so the numbers are
    computed once in a background process (`python -m backtester.risk.prop_card <run id>`, one at a time, the card
    shows "Calculating" with the elapsed time) and stored in `results/<run>/prop_firm.json` (one entry per firm). An
    entry is reused only while its key matches: card version, firm rules (Monte Carlo config), card limits, the run's
    period and a hash of trades.csv; otherwise (or with a missing / broken file) it is recomputed and rewritten.
  - *Full Monte Carlo button:* starts `tools/monte_carlo --run <run id>` (the run's own trades.csv, symbols, period and
    settings.json: no new backtest; it writes one trial-log line (source `run`, family = the strategy or `--family`; started
    from the button it counts as a tried variant, decided by the user 2026-10-20) and check 7 / DSR uses the family's
    trial count like the command-line path; kind B and D use the run's strategy
    and settings) in the background, one at a time, with the running kind (and the path count in kind D), the elapsed
    time and a Cancel (kills the process tree). Job state is on the server, so it survives leaving the page. The report
    (`results/monte_carlo/<run id>/report.html` + `summary.json`) opens in a new tab from `/monte-carlo/<run id>/report.html`;
    that route serves only those two file names inside `results/monte_carlo/`. With a report present the button reads "Run again".
- **Weekend holding / news restrictions:** toggles to be defined then (news needs a calendar data source).
- FTMO rules (2026; re-check before use, presets stay editable):

| | 2-Step (preferred) | 1-Step |
|---|---|---|
| Profit target | P1 10%, P2 5%, funded none | 10% |
| Daily loss | 5% | 3% |
| Max loss | 10%, static | 10%, end-of-day trailing |
| Other | min. 4 trading days | Best Day Rule: best day ≤ 50% of positive days' profit |

The daily loss counts closed trades plus floating P/L and resets at midnight Europe/Prague.
Daily loss is day-start balance minus current equity; its monetary limit is the daily-loss
percentage x initial balance (rule set by the user, 2026-10-22). The personal daily stop remains
a percentage of the day-start balance.

## Components (`risk/`)
1. **RiskConfig** (`config.py`): all settings above, plus per-symbol contract specs and costs. Fully editable in the UI.
2. **PositionSizer** (`sizer.py`): lots per trade and per TP part (› Account & sizing).
3. **AccountSimulator** (`account_sim.py`): › Account simulator.
4. **MonteCarlo** (`monte_carlo.py`): › Monte Carlo.
5. **RiskSweep** (`sweep.py`): › Risk sweep.
6. **PropFirmRules** (`prop_rules.py`): FTMO presets and custom; used only by the prop-firm field (later).
