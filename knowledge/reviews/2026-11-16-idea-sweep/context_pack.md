# Context pack: idea sweep 2026-11-16

Repo: X:\Daten\02_Projekte\01_Laufend\backtester-claude\backtester-claude_V2 (read-only for scouts and Fable).

## Goals
- Goal 1: rule-based strategies that pass prop-firm rules (FTMO 2-step: +10 % / +5 % targets, 10 % max loss,
  5 % daily loss; CFDs on FX, indices, metals, energies, crypto, ~46 US share CFDs). A strategy needs roughly
  300 trades a year at a small positive edge, or fewer trades with a large edge. Crypto prop firms (HyroTrader,
  Crypto Fund Trader on Bybit perps) are also a route.
- Goal 2: exchange futures, swing and other strategies (judged on futures prices with a futures cost model).
- Long-run goal: a portfolio of strategies that balances itself across market regimes.

## Method (fixed)
- Development before 2021-09-14 (CFD / FX / index); crypto develops 2020-2023 and tests once on 2024+.
- Every idea is pre-registered (kill criteria before data), screened net of real costs (doubled-cost check),
  needs t >= 3.0, stable halves, and gets ONE out-of-sample test only.
- Power check before any data look: if the minimum detectable effect (MDE) is above the halved published effect,
  the idea is closed without a look.

## Data already owned (free; no new subscriptions)
- MT5 / FTMO M1 bars: AUDJPY AUDUSD AUS200 BTCUSD CADJPY CHFJPY DXY ETHUSD EU50 EURAUD EURGBP EURJPY EURUSD GBPAUD
  GBPJPY GBPUSD GER40 HK50 JP225 NAS100 NATGAS NZDJPY NZDUSD UK100 UKOIL US2000 US30 US500 USDCAD USDCHF USDJPY
  USOIL XAGUSD XAUUSD (FTMO history mostly from ~2019-20; spread table per hour).
- histdata.com M1 FX / metals / indices back to ~2000s.
- Binance: spot and USDT-M perps klines (wide universe incl. delisted), 1h, aggTrades, taker-flow, funding; Bybit.
- Alpaca (free account): US share / ETF minute bars 2016+: SPY QQQ IWM DIA, 11 sector ETFs, ~46 large caps
  (download in progress).
- Yahoo daily for ~30 large caps; SqueezeMetrics DIX / GEX daily.

## What survived (all crypto, cross-sectional, weekly, flow-based)
- I-73 cross-sectional funding carry on 17 Binance perps: test passed (+112 bp/week, t 2.93, pooled t 3.08).
- I-78 weekly taker-flow imbalance sort on all USDT perps (Strategy 20): test passed +147 bp/week, t 3.76;
  tail-driven. I-83 absorption sort: passed, corr 0.83 with Strategy 20. FB-017 liquid top-100 variant: t 3.64.
- These are now forward logs; a crypto prop firm for Strategy 20 is a money decision for the user.

## What died (pattern)
- Intraday price-pattern / ICT / session sweeps / ORB / gap fade / no-wick on FTMO CFDs: falsified, cost wall
  (spread + commission eats a gross edge of 1-4 bp; ICT levels behave like random levels).
- Calendar / seasonality (turn of month, pre-holiday, pre-FOMC, weekdays): killed on t < 3 or below cost.
- Event studies with few events (FOMC, EIA, auctions, index reviews, unlocks): closed on power (MDE too big).
- Multi-day CFD holds: swap / financing eats the premium (carry, crypto CFD swap -30 %/yr).
- Crypto momentum / trend (C2, I-97), listings (I-81), single-name shock reversal: killed.
- Signal-research stop rule: K = 10 falsified goal-1 signal screens reached 2026-11-15.

## Files with the details
- Ledger (190 rows, every idea and verdict): research/ledger.csv (scouts got a compact copy)
- Previous Fable directions list (43 rows, 2026-11-14): knowledge/reviews/2026-11-14-fable-research-directions.md
- Idea backlog: knowledge/ideas.md; research log: docs/research-log.md; state: docs/HANDOFF.md
- Backtest checklist: knowledge/topics/testing-and-robustness.md
