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

## Forward check

From 2026-11-16, log the book every week without orders. Pre-registered forward kill: after 52 weeks, a net mean
<= 0 or a drawdown worse than -2,200 bp (1.5 x the test's -1,455) closes the strategy. 52 weeks cannot confirm it
(standard error ~66 bp a week at the test sd 474); they can only catch a break.

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
