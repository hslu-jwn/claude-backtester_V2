# Strategy 20: Crypto taker-flow sort (cross-sectional, all Binance USD-M USDT perpetuals)

Status (2026-11-14): **one-time test PASSED** (idea I-78, `knowledge/ideas.md`; ledger `I78`). Build of the research
tool and a forward paper log on the user's go ("Yes, build it", 2026-11-14). The rule below is the **frozen tested
rule**; any change is a new, counted hypothesis with no clean test data left (forward data only). Not tradeable on
FTMO; nothing here places orders.

## Source and mechanism

Fable 5.2 advisory list, row 9 (`knowledge/reviews/2026-11-14-fable-research-directions.md`; label ORIGINAL).
One-sided aggressive (taker) flow over a week, from liquidations, worked orders or attention buying, is followed by
more of the same: coins with the most net taker buying outperform those with the most net taker selling. The sign
was not assumed (two-sided development test); development chose "long the buyers". About half of the edge is the
long leg catching weekly pumps in small perps; the rest (~+56 bp a week with member returns capped at 30 %) is the
same in development and test. Correlation 0.56 with a 1-week past-return sort: partly a short-term momentum proxy.

## Venue, data, costs

- Venue: Binance USD-M perpetuals (AGENTS.md › Venues: futures prices, futures costs).
- Data: daily klines (open, close, volume, quote volume, taker buy volume) and funding of **every** USDT-margined
  perp on data.binance.vision, delisted ones included: `data/cache/binance_wide/` (development months) and
  `data/cache/binance_wide_test/` (2024-01 onward), written by
  `research/screens/2026-11-14_binance_wide_download.py`.
- Costs: taker 0.05 % per side, both legs fully turned over every week: **20 bp a week** per unit on each side.
  Funding of every settlement strictly inside the hold (a long pays a positive rate, a short receives it). No spread,
  slippage or position limits modelled (A2).

## Rule (frozen; crypto split: development 2020-01-01 .. 2023-12-31, test from 2024-01-01)

1. Every Monday 00:00 UTC, **eligible** = USDT perps (no dated quarterlies) with at least 60 daily bars before the
   Monday, a Monday bar, a median daily quote volume of at least 5 million USDT over the last 30 bars before the
   Monday, and all 7 daily bars of the previous week (Monday .. Sunday). A week needs at least 20 eligible symbols
   (else no book); a symbol with no signal (rule 2) still counts toward the 20, as tested.
2. **Signal** from those 7 bars: flow = sum(2 x taker buy volume - volume) / sum(volume). A symbol whose 7-bar
   volume sum is 0 has no signal (left out of the sort).
3. Sort ascending by (flow, symbol name); n = floor(symbols with a signal / 5). **Long the n highest, short the n
   lowest**, equal weight; each side = 1 unit.
4. Entry at the **open of the Monday daily bar**; exit at the **close of the next Sunday bar**, or the last close in
   that week if the symbol stops trading (delisted): no member is dropped, no survivorship.
5. Weekly result per unit on each side: price_bp = mean(long returns) - mean(short returns); funding_bp = mean(short
   funding) - mean(long funding), settlements in (Monday 00:00, next Monday 00:00) exclusive; net_bp = price_bp +
   funding_bp - 20.
6. No stop, no take profit, no other exit; full rebalance every week.

## Risk unit (R) and sizing (A3, Opus)

- 1 R = **600 bp** of one side's notional: the development weekly sd of the net (611 bp), rounded, as Strategy 19
  did. One week = one observation (entry Monday 00:00, exit Sunday 23:59, `r_net` = net_bp / 600), the format
  `risk/monte_carlo.py` `build_days` reads.
- Losses are not capped at 1 R: worst development week -1,438 bp (-2.4 R), worst test week -868 bp (-1.4 R); max
  drawdown development -3,815 bp (-6.4 R), test -1,455 bp (-2.4 R).

## Results (bp per unit on each side, net of 20 bp a week)

| Period | Weeks | Net / week | t | Halves | Win % | PF | Max drawdown | At 40 bp |
|---|---|---|---|---|---|---|---|---|
| Development 2020-05-25 .. 2023-12-25 | 186 | +145.0 | 3.24 | +327 / +2 | 58 | 2.08 | -3,815 | +125 |
| Test 2024-01-01 .. 2026-10-19 | 147 | +147.2 | 3.76 | +120 / +174 | 59 | 2.30 | -1,455 | +127 |
| Pooled | 333 | | 4.81 | | | | | |

Member returns capped at +-50 % a week: development +96.5 (t 2.64), test +77.6 (t 2.38); at +-30 %: +57.8 (t 1.83)
and +56.3 (t 1.90). Test legs 34-63 symbols, eligible median 240. Screen:
`research/screens/2026-11-14_i78_crypto_wide_factors_screen.py` (`--test`).

## Build (research tool, like Strategy 19)

`python -m backtester.tools.crypto_flow [--start] [--end] [--out] [--update] [--forward]`: rule in
`strategy/crypto_flow/book.py` (pure, no file access, no engine import), CLI `tools/crypto_flow.py`; `trades.csv`
one row per week, `legs.csv` members. Golden: the screen's development and test numbers exactly. `--update` fetches
the newest complete months (monthly archive files only) into `data/cache/binance_wide_test`, so a forward week is
complete only after its month's files are published (early next month), as for Strategy 19;
`--forward` appends complete weeks from **Monday 2026-11-16** to `research/forward/crypto_flow.csv` (append-only).

## Built 2026-11-15 (research tool)

Codex `gpt-6.1-sol` medium (brief `briefs/crypto_flow.md`; first call stopped correctly on three spec / screen
conflicts, fixed in 6ae5af9; second call ~13 min, guard ok): `data/binance_wide.py` (readers, monthly updater),
`strategy/crypto_flow/book.py` (pure rule), `tools/crypto_flow.py` (CLI, append-only forward log), 18 tests. Golden:
development 186 weeks +145.0 bp, t 3.24; test 147 weeks +147.2 bp, t 3.76, max drawdown -2.4 R (identical to the
screen). Full suite 5,986 passed.

## Realism check (2026-11-15, diagnostics on spent data; `research/screens/2026-11-15_i78_realism_check.py`)

| | Development | Test |
|---|---|---|
| Net at 20 bp | +145.0 (t 3.24) | +147.2 (t 3.76) |
| Break-even extra slippage per side per member | 36 bp | 37 bp |
| Tiered slippage (< 20 M USDT a day 25 bp, 20-100 M 10 bp, > 100 M 3 bp a side) | +92.8 (t 2.07) | +77.2 (t 1.98) |
| Members below 20 M USDT a day / median member volume | 31 % / 30 M | 56 % / 15 M |
| Most liquid half of the eligible only (a variant) | +232.5 (t 3.65) | +163.0 (t 3.15) |
| ... with tiered slippage | +203.9 (t 3.20) | +124.8 (t 2.42) |

Reading: the edge survives up to ~37 bp of extra slippage per fill; with an assumed tiered slippage it halves to
~+80-90 bp a week (t ~2). It is **not** confined to the illiquid tail: the most liquid half earns as much or more
(a new variant, chosen after seeing the data: forward evidence only, not adopted). Capacity is no issue at retail
size: 100,000 equity at 1 % risk per R is ~350 USDT per member, 0.007 % of the 5 M volume floor. Not checked: real
order books (the tier slippage values are assumptions), Binance position limits on leverage tiers (irrelevant at
1x and this size), delisting settlement prices.

## Combination with Strategy 19 (2026-11-15, diagnostic)

Over the 147 shared test weeks the weekly nets of Strategies 19 and 20 correlate at 0.06; an equal-risk mix gives
+151 bp a week, t 4.30, Sharpe ~2.6 a year, max drawdown -2,330 bp (S19 alone -3,967). S19 failed its replication,
so this only argues for logging both forward.

## Liquid variant FB-017 (frozen 2026-11-15; diagnostic on spent data, forward log only)

Why: HyroTrader caps coins under 100 M USD market cap at 5 % of balance, and capacity. Rule (`knowledge/ideas.md` ›
FB-017): the frozen rule above, except that each Monday the eligible set (rule 1, NaN-signal symbols included) is cut
to the 100 symbols with the highest 30-bar median daily quote volume before the Monday (ties by name) before the sort.
`CryptoFlowConfig(top_volume=100)`; `crypto_flow --liquid [--forward]` (own log `research/forward/crypto_flow_top100.csv`).
Diagnostic (`research/screens/2026-11-15_fb017_liquid_s20.py`): development +171.0 bp a week, t 3.64 (halves +336 /
+41; full +145.0, halves +327 / +2); test (spent) +166.3, t 3.06 (full +147.2, t 3.76), worst week -1,412. Both periods
were seen before, so this is no test; the forward kill below applies to it too.

## Rebalance-day check FB-022 (2026-11-15, diagnostic on spent data; criteria committed before the run)

The frozen book anchored on each weekday (`research/screens/2026-11-15_fb022_s20_rebalance_day.py`), net bp a week
(t): development Mon +145 (3.24), Tue +114 (2.59), Wed +124 (2.71), Thu +85 (1.75), Fri +114 (2.55), Sat +145 (2.93),
Sun +153 (2.93); test Mon +147 (3.76), Tue +104 (2.49), Wed +46 (1.06), Thu +52 (0.93), Fri +137 (3.27), Sat +96
(2.27), Sun +73 (1.82). No anchor <= 0; other-six mean +123 (dev) / +85 (test) >= half of Monday: **robust** by the
pre-set rule. Monday is the luckiest anchor in the test, so the fair expectation for the forward log is the all-anchor
mean, ~+94 bp a week (test) / ~+126 (development), not +147.

## Legs against BTC FB-020 (2026-11-15, diagnostic on spent data)

Each leg hedged with BTCUSDT (beta 1, 12 bp a week; `research/screens/2026-11-15_fb020_s20_long_leg.py`): development
long leg - BTC +141.6 bp a week (t 2.27), BTC - short leg -0.6; test long leg - BTC +5.6 (t 0.10), BTC - short leg
+137.7 (t 2.21). The edge sat in the long leg in 2020-23 and in the short leg in 2024-26: no single-leg version is
reliable; only the long-short book is logged (FB-020 closed).

## Execution FB-273 (2026-11-15, Q4-2023 Mondays, development; card committed before data)

Binance aggTrades at the Monday 00:00 rebalance, 13 Mondays x 4 perps (XEM, BEL, CRV, SOL) x buy and sell
(`research/screens/2026-11-15_fb273_maker_fill.py`): taker now costs 9.9 bp a fill vs P0 (fee 5 + half-spread / tick;
XEM 16.6, CRV 13.4, BEL 5.1, SOL 4.7); maker-first at P0 (60 min, then taker) 12.0 bp: fills 93 %, but the misses cost
~151 bp each (price ran away). Saving -2.1 bp, t -0.44: **keep taker**. The backtest's 20 bp a week assumes 5 bp a
fill; the measured ~10 bp a fill means ~40 bp a week, i.e. a fair forward expectation of ~+74 bp a week (not +94).
The cost default stays 20 bp (a default; the user's call).
**Turnover correction (2026-11-15, Fable call 3 item 1):** the book changes only 53 % (development) / 58 % (test) of
each side a week (one-way, equal weights). Netting the rebalance, ~10 bp a fill costs ~22 bp a week, about the
backtest's 20: the fair forward expectation is **~+92 bp a week** (all-anchor +94 minus ~2), not +74.

## Forward check

From 2026-11-16, log the book every week without orders. Pre-registered forward kill: after 52 weeks, a net mean
<= 0 or a drawdown worse than -2,200 bp (1.5 x the test's -1,455) closes the strategy. 52 weeks cannot confirm it
(standard error ~66 bp a week at the test sd 474); they can only catch a break.


**Bybit prices and funding (2026-11-16, diagnostic on the spent test period;
`research/screens/2026-11-16_s20_bybit_prices.py`):** signal, eligibility and the top-100 cut on Binance volume and
taker flow; each Binance perp listed on Bybit gets Bybit's daily open / close and Bybit's funding from its first Bybit
bar (window from 2023-09); perps not on Bybit dropped. Top-100 book 2024-01..2026-10: **Bybit prices + funding +145.5
bp a week, t 2.93, worst -1,253**; the same coins and days on Binance prices +137.9, t 2.80, worst -1,226. The edge
transfers to the venue a prop account would trade (Bybit-delisted coins still missing).

**Weekday tranches (2026-11-15, prop decision package):** `crypto_flow --liquid --anchor <mon..sun> --forward` logs the
same frozen book rebalanced at 00:00 UTC on each weekday into `research/forward/crypto_flow_top100_<day>.csv` (Monday
keeps `crypto_flow_top100.csv`); the tranched account is the mean of the seven. The FB-254 boundary applies to the
Monday book (pre-registered); the tranches are reported beside it, not tested separately.

**Sequential boundary (FB-254, pre-registered 2026-11-15 before any forward week):** a look every 13 weeks up to 104
(8 looks); z = net mean / (sd / sqrt(n)) over the completed looks. Confirmed when z >= 2.071 / sqrt(k / 8)
(O'Brien-Fleming, one-sided 2.5 %: 5.86, 4.14, 3.38, 2.93, 2.62, 2.39, 2.21, 2.07); killed early when z <= -2 at any
look; the 52-week kill above stays. `research/screens/2026-11-15_fb254_forward_boundaries.py --check`. Power at the fair +74 bp (sd 474): 34 % confirmed by week 104 (top-100 variant, sd 658: 20 %); a
confirmation needs ~+96 bp a week over 104 weeks.

## Assumptions (decided by Opus)

- A1: weekly rebalancing (Fable row 9 said daily; at 20 bp a day the effect would need more than 20 bp a day).
- A2: costs are taker fees only. The edge sits partly in small, pumping perps where real spreads, slippage,
  Binance position limits and leverage cuts before delisting bite; doubled costs stay +127 in the test, but a
  pump that cannot be bought at size is not measured. A realism check is the next research step.
- A3: R = 600 bp of one side's notional (above); a risk unit, not a stop.
- A4: a member that stops trading exits at its last close in the week (delisting); funding is counted for every
  settlement in (Monday 00:00, next Monday 00:00) as tested (corrected 2026-11-14 on Codex's question: the first
  draft said "not counted after the last bar", which the screen never did).
- A5: ties broken by symbol name (stable sort on (flow, symbol)), exactly as tested.
