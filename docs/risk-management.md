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

### Costs (per symbol)
- ⚙️ **Spread:** a **fixed value per symbol** for every pair (histdata.com has no ask prices, user 2026-10-10). Defaults (estimates until FTMO's spreads are measured): NAS100 **1.0** point, US500 **0.5** point, XAUUSD 0.25, GBPUSD 0.3 pip, GBPJPY 1.0 pip.
- ⚙️ **Commission** (per lot, round turn) and ⚙️ **swap** (per lot per night, long and short): per-symbol fields, to be updated from MT5/FTMO. Commission defaults (user, 2026-10-10, as ROADMAP 3.1): XAUUSD **$6**, GBPUSD / GBPJPY **$5**, NAS100 / US500 **0**.
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
  DXY, NATGAS **0**, BTCUSD / ETHUSD 0 (FTMO charges crypto as a percentage; not modelled), all to be confirmed by the user.
  BTCUSD / ETHUSD swap is a percentage-per-year mode in MT5 (-30 %): **0 here**, needs a price-proportional swap model.

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
  | BTCUSD / ETHUSD | 1.0 / 0.6 | 1 / 10 | 1 | 0 / 0 (see above) | Fri |

  **PLACEHOLDER, to be confirmed by the user (ROADMAP 11.9): Binance futures BTCUSDT / ETHUSDT.** Taker fee **0.05 % per side** entered
  as dollars per lot (1 coin) at a fixed reference price (BTC 100,000 -> $100 round turn, ETH 4,000 -> $4); this is wrong in years with
  other prices because a percentage of the notional is not modelled. Spread 0, swap 0 (funding from `data/cache/binance_funding` is not
  applied yet). Do not trust crypto net R until the user has confirmed or replaced these values.
- ⚙️ **Cost filter** (user, 2026-10-14: build it in the engine, off by default; details chosen by Claude; knowledge base
  I-45 cost-to-target): `CostConfig.max_cost_r`, default **0 = off**. An order whose spread + commission in R at its fill
  (spread / SL distance + commission as a price distance / SL distance; only the costs that are switched on; no swap, no
  slippage) is **above** this value is not filled. The engine tells the strategy (`Strategy.on_order_skipped(ref, now)`,
  default: nothing): strategy 2 counts no trade for it and keeps the setup open for a later entry; strategy 4 stays flat
  and the next signal event tries again. Equal to the limit is filled. Strategies 1 and 3 have no hook yet: for their
  per-session limits a skipped order counts as taken (both are paused / dropped). The filter studied on strategy 2's
  trades: ROADMAP 10.5.
- ⚙️ **Slippage** in points per fill, applied to **entries and SL hits** (market fills); TPs are limit orders, no slippage. Defaults (rough starting estimates, to be checked against FTMO demo fills):

  | Symbol | Slippage per fill |
  |---|---|
  | NAS100 | 1.0 point |
  | US500 | 0.25 point |
  | XAUUSD | 0.10 |
  | GBPUSD | 0.2 pip |
  | GBPJPY | 0.3 pip |

- Break-even "including costs" (strategy rules) uses the same spread, commission and slippage.

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
- Reshuffles the order of **whole trading days** (not single trades, so bad days stay realistic) ⚙️ **1,000** times (default) and simulates the account for each order with the same settings.
- **Output:** distribution of max drawdown and final balance, e.g. "in 95% of the runs the max drawdown stays below X%", a fan of simulated equity curves. Main use: choosing a safe risk %.

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
- **Weekend holding / news restrictions:** toggles to be defined then (news needs a calendar data source).
- FTMO rules (2026; re-check before use, presets stay editable):

| | 2-Step (preferred) | 1-Step |
|---|---|---|
| Profit target | P1 10%, P2 5%, funded none | 10% |
| Daily loss | 5% | 3% |
| Max loss | 10%, static | 10%, end-of-day trailing |
| Other | min. 4 trading days | Best Day Rule: best day ≤ 50% of positive days' profit |

The daily loss counts closed trades plus floating P/L and resets at midnight CE(S)T.

## Components (`risk/`)
1. **RiskConfig** (`config.py`): all settings above, plus per-symbol contract specs and costs. Fully editable in the UI.
2. **PositionSizer** (`sizer.py`): lots per trade and per TP part (› Account & sizing).
3. **AccountSimulator** (`account_sim.py`): › Account simulator.
4. **MonteCarlo** (`monte_carlo.py`): › Monte Carlo.
5. **RiskSweep** (`sweep.py`): › Risk sweep.
6. **PropFirmRules** (`prop_rules.py`): FTMO presets and custom; used only by the prop-firm field (later).
