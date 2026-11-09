# Deferred platform-data capability audit

Date: 2026-11-03  
Scope: read-only V2 source/documentation audit; no cache contents or results opened  
Verdict: **Treasury-specific and point-in-time cross-sectional equity research remain correctly
deferred; neither can be represented faithfully by the current symbol/data contracts.**

## Treasury instruments

V2's canonical source map contains FX/CFD metals, equity indices, energy, DXY, crypto, and Binance
crypto futures. It contains no Treasury cash security, note/bond future, yield series, duration,
contract-roll schedule, conversion factor, cheapest-to-deliver mapping, accrued interest, coupon,
or Treasury-specific cost model. The MT5 default aliases and `CostConfig` likewise contain no
Treasury instrument.

Consequences:

- R006's auction-pressure evidence cannot be proxied through DXY, US500, gold, or a generic rate
  narrative; those are different estimands.
- A price-only yield proxy would reverse/warp price exposure and omit duration/roll mechanics.
- A faithful futures study would need an immutable continuous-contract construction or explicit
  delivery-month series, roll rule fixed before outcomes, tick/contract value, commissions,
  session/holiday calendar, and point-in-time Treasury auction schedule.

## Cross-sectional equities and ETFs

`SymbolSources` maps one named symbol to one cache stream. The current universe has no constituent
membership table, security master, delisting history, split/dividend/corporate-action stream,
point-in-time sector/industry data, borrow/shortability history, or portfolio-level synchronized
quote contract. V2's own interface review states that dividend-adjusted prices are absent and that
ETF absolute momentum requires an adjusted total-return adapter.

Consequences:

- Same-clock evidence ranking hundreds of stocks cannot be adapted to a single index CFD.
- Aleti, Bollerslev, and Siggaard's factor-zoo result cannot be reduced to index OHLC: its causal
  predictor panel contains 218 characteristic portfolios, 48 industries, and six standard factors
  synchronized at 15-minute frequency, followed by a continuous-versus-jump transform and fitted
  regularized/ML models. V2 supplies none of those point-in-time portfolio series or model inputs.
- The paper trades SPY with TAQ quoted-spread costs and initializes the first intraday weight from
  an overnight long position. A flat-at-open US500 CFD adaptation would change both execution and
  turnover accounting even if the predictor panel existed.
- A present-day constituent list would introduce survivorship bias; unadjusted prices would
  introduce corporate-action artifacts.
- ETF_ABSMOM_12M_LC remains unsupported both for adjusted total-return data and its monthly
  target-weight accounting. Its retained draft is not a runnable approximation.

## Required expansion gates

Treasury research would require a separately supported instrument mandate plus versioned price,
roll, cost, calendar, and auction datasets. Cross-sectional research would require point-in-time
membership/security-master/corporate-action data, synchronized prices, execution/shorting rules,
portfolio accounting, immutable characteristic/industry/factor definitions, reproducible
portfolio construction, the declared high-frequency transforms/models, and ETF-specific cost and
opening-position semantics. Each expansion would need its own no-lookahead conformance fixtures
and development/holdout protocol before a hypothesis is designed around it.

No current high-priority candidate justifies either expansion. Keep both rows deferred rather than
creating proxy strategies, implementation requests, or data downloads.
