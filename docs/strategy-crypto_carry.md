# Strategy 19: Crypto funding carry (cross-sectional, Binance USD-M perpetuals)

Status (2026-11-14): spec **accepted by the user 2026-11-14** ("Yes, all three": R = 1,000 bp risk unit without a
stop, build the research tool, forward paper log). **One-time test PASSED** (idea I-73, `knowledge/ideas.md`; ledger `I73`). Spec written on
the user's go ("Yes, write the spec") for review; nothing is built yet. The rule below is the **frozen tested
rule**; any change to it is a new, counted hypothesis with no clean test data left (forward data only).

## Source and mechanism

Schmeling, Schrimpf & Todorov, "Crypto carry", BIS Working Paper 1087 (2023, rev. 2025), read in full: on BTC / ETH
dated futures (2019-03 to 2022-01) a high carry (futures over spot) predicts lower spot and futures prices, more
sell liquidations and more negative skew (crash risk). Carry is driven by trend-chasing small investors who pay
for leverage, and by scarce arbitrage capital. Our adaptation (label ADAPTATION): perpetual funding is the
carry, ranked across coins. The short side holds the most crowded leveraged longs, collects their funding and
sits on the side the paper says the price moves; the long side pays the least funding.

## Venue, data, costs

- Venue: Binance USD-M perpetual futures (AGENTS.md › Venues: futures prices, futures costs, no CFD swap).
  Not tradeable on FTMO.
- Prices: `data/cache/binance/<SYM>` (last-trade M1, bid = ask). Funding: `data/cache/binance_funding/<SYM>.csv`.
- Costs: taker 0.05 % per side (`engine/costs.py`, Binance's published regular-user rate, checked 2026-11-13),
  so 10 bp per leg per round trip and **20 bp a week per unit on each side**. Funding of every settlement a leg
  is open over: a short receives a positive rate, a long pays it. No spread, no slippage modelled.

## Universe

BTC, ETH, BCH, XRP, EOS, LTC, TRX, ETC, LINK, XLM, ADA, BNB, XTZ, XMR, NEO, DASH, ATOM (all `…USDT`): every USD-M
perp listed by January 2020 plus the six largest February 2020 listings (chosen 2026-11-13 by listing date, before
any data was read; delisted symbols stay in). A symbol is eligible on a Monday once it has 30 days of funding
history and at least 21 settled rates.

## Rule (frozen)

1. Every Monday at 00:00 UTC, right after the 00:00 settlement, compute for each eligible symbol the funding
   accrued in the last 7 days: the sum of the rates settled in (Monday - 7 d, Monday], the 00:00 print included.
   For 8 h symbols this ranks exactly like the mean of the last 21 rates.
2. Rank by that sum. **Short the 4 highest, long the 4 lowest**, equal notional per leg (each side = 1 unit,
   each leg 1/4 unit). Fewer than 8 eligible symbols: no book that week.
3. Entry at the close of the M1 bar ending 00:01 (the bar opening at 00:00). Exit at the close of the bar ending
   Sunday 23:59, before the next Monday settlement. Full rebalance every week, even for a leg that stays.
4. A symbol without its entry or exit bar is dropped from that week's leg; the leg keeps its other members.
5. No stop, no take profit, no other exit.
6. Weekly result per unit on each side = mean long-leg return - mean short-leg return + funding received - funding
   paid - 20 bp.

## Risk unit (R) and sizing (Opus's proposal, for the user's review)

- The tested rule has **no stop**, so R cannot be a stop distance. Development data shows why a disaster stop
  does not help: short legs moved up to +156 % against the position inside one week (BNBUSDT, week of
  2021-02-15; 99th percentile 85 %), long legs down to -71 %. A stop that history never hits would sit beyond
  that and mean nothing.
- **Proposal:** 1 R = 1,000 bp of one side's notional, the development-period weekly sd of the book (960 bp,
  rounded), fixed before the test was read. Each week is one observation: entry Monday 00:01, exit Sunday 23:59,
  `r_net` = weekly net bp / 1,000. That is the format the risk tools already read (`risk/monte_carlo.py`
  `build_days`: `entry_time`, `exit_time`, `r_net`), so no engine change is needed.
- **Losses are not capped at 1 R:** worst test week -3.2 R; max drawdown -4.0 R. The spec reports this every time;
  a "risk 1 %" setting means a 1-sd week costs about 1 % of equity, not a maximum loss.
- **Sizing:** notional per side = risk per R × equity / 10 %. Example: 0.5 % risk per R → 5 % of equity per side,
  10 % gross; worst test week -1.6 % of equity, max drawdown about -2 %.
- **Margin:** cross margin. At gross notional ≤ 1× equity, the +156 % leg move cannot liquidate the account
  (one short leg at 1/8 of gross would lose ~20 % of equity at 1× gross). Leverage above 1× gross needs the user's
  decision.

## Results (all in bp per unit on each side, net of 20 bp a week)

| Period | Weeks | Net / week | t | Price part | Funding part | Halves | Worst week |
|---|---|---|---|---|---|---|---|
| Development 2020-02-17 .. 2021-09-06 | 82 | +138 | 1.30 | +106 | +52 | +2 / +274 | -2,626 |
| Test 2021-09-20 .. 2026-10-19 | 266 | +112 | 2.93 | +103 | +29 | +105 / +119 | -3,159 |
| Pooled | 348 | | 3.08 | | | | |

Test: 55 % winning weeks, profit factor 1.72, doubled costs +92, without the 2 best weeks +95, without BTC / ETH
+102, max drawdown -3,967 bp, longest losing run 7 weeks; years 2021 +139, 2022 +144, 2023 -18, 2024 +167,
2025 +199, 2026 +46. Development gate failed (t 1.30 < 3.0; power: t 3 needed ~300 bp a week); the test was spent
on the user's decision with five pre-registered gates, all passed. Data check: EOS prices end 2025-05-21 while
its funding continues as a constant placeholder; ranking only symbols with an entry bar gives +110, t 2.98.
Script: `research/screens/2026-11-13_i73_crypto_carry_xs_screen.py` (`--test`).

## Built 2026-11-14 (research tool)

`python -m backtester.tools.crypto_carry [--start] [--end] [--out] [--update] [--forward]`; rule in
`strategy/crypto_carry/book.py` (pure, no engine import), CLI `tools/crypto_carry.py`; one row per week in
`trades.csv`, members in `legs.csv`. Golden check: development 82 weeks +138.0 bp, test 266 weeks +112.0 bp,
t 2.93 (identical to the screen). `--update` fetches only the last 3 months of klines + funding (the history is
cached); `--forward` appends complete weeks from 2026-11-16 to `research/forward/crypto_carry.csv` (append-only;
a changed past week stops it). A symbol whose funding stopped 7+ days before the newest print of any symbol
(delisted) stays ranked, as frozen, but does not hold a week back; a feed that lags for all symbols does.
Funding comes from the monthly archive files, so a forward week is complete only after its month's funding
file is published (early next month).

**Monte Carlo, test weeks (risk/monte_carlo.py, block bootstrap 20 days, 1,000 runs, 100,000 start; it resamples
the observed test edge, so it is optimistic):**

| Risk per R | Notional per side | Median gain (5.1 years) | p5 / p95 gain | Max drawdown median / p95 | Worst week |
|---|---|---|---|---|---|
| 0.5 % | 5 % | +16 % | +7 / +26 % | 2.3 / 4.1 % | -1.6 % |
| 1 % | 10 % | +34 % | +14 / +57 % | 4.6 / 8.1 % | -3.2 % |
| 2 % | 20 % | +78 % | +28 / +144 % | 9.2 / 15.7 % | -6.3 % |

Profitable months 67 %; longest losing streak median 6 weeks (max 14); longest drawdown median ~230 days.

## Build plan (needs the user's go: ROADMAP V2.10 › C baskets "only on the user's go")

Smallest version: a research tool, not an engine strategy.

1. `research`-side module that turns the frozen rule into weekly book observations: `trades.csv` with one row per
   week (`entry_time`, `exit_time`, `r_gross`, `r_net`, cost and funding parts) plus `legs.csv` (symbol, side,
   signal, price return, funding per leg), from the cache through `SymbolSources` (no direct parquet paths).
2. Feed `trades.csv` to the existing Monte Carlo, bootstrap and drawdown tools at the sizing above.
3. Tests first (hand-built fixtures): ranking and leg choice with ties (ASSUMPTION: a tie is broken by symbol
   name); the signal uses only rates settled at or before Monday 00:00 (no-lookahead test: appending later
   funding or prices never changes an emitted week); a missing entry / exit bar drops the leg member; a symbol
   with 4 h funding sums 7 days; fewer than 8 eligible symbols gives no week; reproduce the screen's development
   and test numbers exactly (golden check).

## Forward check (proposal)

The test data is spent. Evidence from here on is forward data only: from the first Monday after the user's go,
log the book every Monday (signal, legs, entry and exit prices, funding) without orders, and report it with the
weekly evening summary. Pre-registered forward kill: after 52 weeks, a net mean <= 0 or a drawdown worse than
-6 R (1.5 × the test's) closes the strategy. 52 weeks cannot confirm it (standard error ~87 bp a week); they
can only catch a break.

## Assumptions (decided by Opus)

- A1 (2026-11-14, before the test): signal = funding accrued over 7 days, not the mean of the last 21 rates, so
  XTZUSDT's 4 h / 1 h funding from 2025-07-20 still covers 7 days. Identical ranking in development (all 8 h).
- A2: costs are taker fees only; no spread or slippage on last-trade prices. Entries fall in the settlement
  minute's volatility spike (crypto intraday report S4); slippage there is not measured. Doubled costs stay +92.
- A3: R = 1,000 bp of one side's notional (above); a risk unit, not a stop.
- A4: delisted symbols stay in the universe; a symbol without bars is dropped from the leg, not replaced.
- A5 (corrected 2026-11-14 by the build's golden check): ties are common (many symbols sit at the 0.01 % default
  rate, so equal 7-day sums). The tested screen sorts by the signal only (stable sort) in the universe order above:
  among tied symbols the longs take the earliest in that order, the shorts the latest. That is the frozen rule.
  The first draft's "ties by symbol name" would change 10 development weeks (development +124 bp, t 1.17; test
  +110 bp, t 2.92): an untested variant, not used; it shows the test result does not hinge on the tie order.

## Decisions by the user (2026-11-14, "Yes, all three")

1. R = 1,000 bp of one side's notional, a risk unit without a stop (A3).
2. Build the research tool (C baskets, research tool only).
3. Forward paper log (no orders) from Monday 2026-11-16, the first Monday after the go.
