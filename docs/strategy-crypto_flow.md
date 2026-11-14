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
   Monday, a Monday bar, and a median daily quote volume of at least 5 million USDT over the last 30 bars before the
   Monday. A week needs at least 20 eligible symbols (else no book).
2. **Signal** from the 7 daily bars before the Monday (Monday .. Sunday of the previous week; all 7 required):
   flow = sum(2 x taker buy volume - volume) / sum(volume). A symbol whose 7-bar volume sum is 0 has no signal.
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
the newest months (monthly archive files, and daily files for the running month) into `data/cache/binance_wide_test`;
`--forward` appends complete weeks from **Monday 2026-11-16** to `research/forward/crypto_flow.csv` (append-only).

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
- A4: a member that stops trading exits at its last close in the week (delisting); funding after that is not
  counted.
- A5: ties broken by symbol name (stable sort on (flow, symbol)), exactly as tested.
