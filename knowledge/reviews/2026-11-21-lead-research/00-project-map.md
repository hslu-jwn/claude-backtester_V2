# Project map and gap audit

## Current state

The native registry contains 14 strategies, while the research ledger contains 278 records. The ledger is
dominated by rejected, parked, and screened ideas: 112 rejected, 54 parked, 52 screened, 23 development-tested,
10 tested, 2 test-spent, and only 1 forward row. The 252 recorded native trials are especially concentrated in
timed holds, the US-close/German-open family, opening-range breakout, and trend following.

The authoritative survivors are:

- **Strategy 20 / I-78, weekly crypto taker-flow sort:** test +147.2 bp/week, `t=3.76`; still tail-driven and
  assigned a shrunk planning expectation of roughly +60 to +90 bp/week.
- **I-109, Treasury month-end duration:** test +24.9 bp, `t=2.14`; not a blind test, now a forward/manual Micro
  10-Year path.
- **Strategy 19, crypto carry:** forward-only and M1 `UNPROVEN-POSITIVE`. I-73's one-time test was positive
  (`t=2.93`) but did not meet the confirmation threshold alone, and its broader replication failed. I-83 reused the
  test period and correlates 0.83 with I-78, so it is not an independent stream.

There is no goal-1/FTMO stream. Frozen shelf periods start 2026-11-18 for the share/event rows and 2026-11-23 for
crypto weeks; the scheduled logger first collects them on 2026-12-03.

## Families already searched deeply

| Family | Project conclusion |
|---|---|
| CFD session zones, sweeps, candle geometry, gaps, ORB, clocks | falsified, rejected, or cost-dominated |
| Trend and generic momentum | Kaufman trend falsified; share 12–1 momentum underpowered and killed |
| Daily/intraday reversal | failed gates; H1 shock response had all 18 cells negative |
| Fixes, announcements, calendar windows | London fix and EIA negative; other windows mostly parked or closed |
| Lead-lag and simple relative value | US close→German open falsified; FX/metal/crypto lead-lag families rejected |
| Commodity curve and futures roll | plausible research base, blocked by expired-contract/curve data |
| Real-share factors | point-in-time wide universe exists, but history begins effectively in 2016 |

This is why another M15 indicator search has low expected value. The two successful mechanisms are breadth
(crypto cross-sections) and forced, dated flows with enough movement per event (Treasury month-end).

## Supported data and practical boundaries

- Engine bars: M1, M5, M15, M30, H1, H4, D1, and W1, causally resampled from M1.
- CFD cache: 34 active symbols across FX, indices, metals, energy, crypto, and DXY.
- Crypto: Binance minute/hour/day bars, funding, taker flow, and wide/delisted perp universes.
- Shares: point-in-time top-1,000 US common-stock universe; Alpaca SIP daily bars from 2016 and narrow M1 windows
  fetched by date. Bars are split-adjusted, not dividend-adjusted; historical borrow and delisting realism remain
  limitations.
- Rates/futures: FRED yields, Treasury data, Cboe VX, EIA strips, and some continuous series. Broad free
  per-contract history is unavailable.
- The macro/news calendar has known timestamp and coverage defects and cannot support a clean conditional study.

## Binding gaps, in order

1. **Forward evidence:** existing candidates need untouched observations more than new parameter work.
2. **Long, point-in-time non-CFD data:** this blocks source-matched stock factors and curve/roll strategies.
3. **Execution realism:** stressed slippage, placeholder GBPUSD spreads, and dividends can decide marginal edges.
   For a Swiss resident, after-tax returns also need a professional-trader scenario: the federal safe-harbour
   criteria are cumulative and non-hedging derivatives fail one criterion, although failure does not automatically
   determine status.
4. **Multi-symbol portfolio integration:** the untested weekly FX relative-strength spec is blocked on basket
   execution, not idea generation.
5. **Research governance:** `docs/HANDOFF.md` and the ledger are authoritative; a stale roadmap sentence still
   describes trend following as a candidate even though S04 is falsified.

## Immediate execution-quality levers

- **Correct I-105 before forward logging.** The frozen signal ranks on the official opening price and claims entry
  at that same opening auction. Alpaca rejects opening-auction orders after 09:28 ET, before the opening print is
  known. The rule is therefore look-ahead/non-executable as written; an executable pre-open signal or a later
  continuous-market entry is a new rule and must be frozen before observing forward returns.
- Use Alpaca's official auction endpoint whenever a share rule claims market-on-open or market-on-close
  execution. The project's own audit found daily opens differ from official auction prints by a median 3.4 bp
  and p90 23 bp—enough to reverse a marginal result.
- Use Dukascopy historical bid/ask data only as an independent tail-spread stress for placeholder FTMO years. It
  cannot replace venue-specific FTMO costs, but it can reveal understated thin-hour and news-event spread tails.
- **Use a narrowly scoped Databento credit for I-109 implementation evidence, if the user wants an account.** New
  teams currently receive $125 of historical credit; price each classic-ZN/Micro-10Y request with `get_cost` before
  downloading. Pull only definitions, statistics, and M1 windows around the registered month-ends. This can validate
  rolls, the 15:00 spread, and executable fills; it is not a new return test. A portal monthly limit blocks requests
  only after usage exceeds the limit, so it is not a guaranteed zero-overshoot cap.
- **Treat Binance USDC-perp zero-maker pricing as a forward execution scout, not a correction to Strategy 20.** The
  promotion is revocable, Swiss availability and weekly symbol overlap are unverified, and the frozen strategy uses
  USDT perps with taker fills. Even perfect coverage at roughly 55% one-way turnover saves only about 11 bp/week
  against the assumed 5 bp fee; the project's prior passive-fill study was adverse. Any A/B needs missed fills,
  spread, funding, USDC/USDT basis, and a separately frozen forward log.
