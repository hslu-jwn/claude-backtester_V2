# Card 6 step A: Hyperliquid public-API audit (signal-free, 2026-11-17)

Script: `research/screens/2026-11-17_card6a_hyperliquid_audit.py` (public `info` endpoint, no key; daily candles cached,
git-ignored, in `data/cache/hyperliquid/candles_1d/`). No return, funding sign or sort was computed.

| Item | Finding |
|---|---|
| Perps | 235 listed, 56 of them delisted; **every delisted perp still returns its daily candles** (no survivorship gap) |
| History | candles requested from 2022-01-01 (41 perps start exactly there, so earlier bars may exist; irrelevant, see the next rows); funding history from 2023-05-12 |
| New listings by year | 2022: 54, 2023: 63, 2024: 59, 2025: 51, 2026: 8; delistings 2024: 12, 2025: 25, 2026: 19 |
| Strategy 20's liquidity rule (>= 60 bars, 30-day median quote volume >= 5 M USD) | median 22 eligible per Monday; >= 20 eligible on **105 Mondays** (2024-03-04 .. 2026-11-16), >= 30 on 51, >= 40 on only 4 |

## What it means

- **Step B (card 1's carry rule, needs >= 40 names a week): closed on data.** 4 weeks; card 1 was KILLED anyway.
- **Step C (Strategy 20's frozen flow rule, >= 20 names a week):** at most ~105 weeks (2024-03..). Power: at the weekly
  sd of 474-658 bp the standard error is 46-64 bp; the replication kill t < 2.0 needs ~93-128 bp a week. At Strategy 20's
  test effect (+147) the expected t is ~2.3-3.2; at the planning value (+74) ~1.2-1.6. A real but modest check:
  it would catch a Binance-only artefact, it cannot confirm a small edge. Every forward week adds to it.
- The AWS decision (requester-pays S3 fills, HANDOFF › Open 7) can use these numbers. Unverified: the S3 fill
  history depth and the transfer cost.
