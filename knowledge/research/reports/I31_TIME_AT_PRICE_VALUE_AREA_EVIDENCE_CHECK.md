# I-31 time-at-price value-area evidence check

Date: 2026-10-29  
Decision: **park; do not create a strategy draft or add a value-area overlay**.

## Question

Does independent evidence support the frozen I-31 proposal to build a prior-session 70% value area
and point of control from M1 time-at-price, then follow breaks or fade failed excursions back toward
the point of control?

Time Price Opportunity (TPO) and executed volume-at-price were kept separate. Evidence requiring
centralized futures volume, tick order flow, footprint imbalance, or a learned model does not validate
an OHLC-only M1 occupancy rule.

## Evidence inspected

- Theo Howard, “Stop Distance, Exit Methodology, and Signal Preservation in Intraday Value Area
  Breakouts: Evidence from E-mini S&P 500 Futures,” 2026,
  [SSRN abstract and metadata](https://ssrn.com/abstract=6350238),
  [DOI](https://doi.org/10.2139/ssrn.6350238). **Abstract opened; full PDF fetch was blocked.**
  This independent, non-peer-reviewed study is the closest systematic breakout test found. It uses
  one-second ES trades, 6,284 events, and 13 months from January 2025 through January 2026. Its
  unfiltered volume-profile continuation signal averages -2.20 ticks and is insignificant with
  day-clustered errors (t=-1.37, p=0.17); excluding one regime month leaves -0.19 ticks (p=0.74).
  Twelve price-stop distances destroy value relative to the unmanaged horizon. Post-hoc depth and
  time-exit findings do not turn the failed unconditional signal into a preregistration anchor.

- Fabio La Manna, “Reframing TPO as an Estimator of Moments and Entropy of Equity Markets,” 2026,
  [SSRN abstract and metadata](https://ssrn.com/abstract=6974102),
  [DOI](https://doi.org/10.2139/ssrn.6974102). **Abstract opened; full PDF fetch was blocked.**
  The independent, non-peer-reviewed paper treats weekly TPO as a descriptive distributional
  estimator over 489 SPX profiles from January 2015 through June 2026 and checks six ETF/index
  replicants. Its abstract says common POC-magnet and symmetric value-boundary support/resistance
  claims are rejected or materially qualified. It is weekly, does not test I-31's day-flat rule,
  and reports no transferable net trading result.

- Oldřich Šístek, “The Use of Market Profile and Order Flow to Support Intraday Futures Trading,”
  bachelor thesis, Prague University of Economics and Business, 2025,
  [full thesis](https://insis.vse.cz/zp/92005). **Full thesis opened.** It backtests 607 ES trades
  from 30 April 2024 through 1 May 2025 using purchased tick data. Entries require first tests of
  prior naked VAH/VAL/POC levels plus a one-minute footprint absorption signal with bid/ask ratio,
  minimum executed volume, and close-location conditions. It reports a 44% win rate, profit factor
  1.30, and positive gross return with a fixed 3-point stop and 5-point target. Transaction fees are
  explicitly excluded, the stop/target can be user selected and an alternative is inspected, the
  period is one year and one contract, and there is no untouched out-of-sample test. This is a useful
  implementation example, not evidence for time-at-price alone.

- Wei-Yuan Huang, An-Pin Chen, Yu-Hsiang Hsu, Hsin-Yi Chang, and Ming-Wen Tsai, “Applying Market
  Profile Theory to Analyze Financial Big Data and Discover Financial Market Trading Behavior—A
  Case Study of Taiwan Futures Market,” *2016 7th International Conference on Cloud Computing and
  Big Data*, 2017, 166–169, [DOI](https://doi.org/10.1109/CCBD.2016.041).
  **Publisher metadata/abstract-level description opened; full paper not opened.** The work applies
  market-profile features and a back-propagation network to a short Taiwan-futures sample. A learned
  feature model is outside I-31 and adds a large uncounted selection surface.

## Why the proposed rule is not identified

1. **TPO is not executed volume.** Counting M1 bar visits estimates time occupancy. It does not
   recover the centralized volume profile or footprint imbalance used by the positive implementation.
2. **The level does not choose direction.** The same boundary can be framed as acceptance/breakout
   or rejection/fade. “Failed excursion” is undefined until persistence, depth, re-entry, target,
   stop, and timeouts are chosen, creating a broad two-sided search.
3. **The closest unconditional test is null.** Howard's reported ES breakout mean is negative and
   insignificant; favorable conditional refinements are discoveries within that sample.
4. **The POC-magnet premise is not stable.** The TPO study explicitly reports that this practitioner
   belief is rejected or qualified, and neither it nor the thesis establishes a causal pull toward POC.
5. **Positive evidence depends on unsupported data.** The thesis requires tick-level bid/ask volume
   and absorption. V2's OHLC/tick-volume setting cannot reproduce this signal without silently
   substituting a weaker observable.
6. **Costs and execution matter at profile boundaries.** The positive thesis omits 607 trades' fees;
   the closest breakout study finds price stops harmful. A gross backtest cannot resolve net edge.
7. **Construction choices multiply trials.** Session boundary, price-bin size, TPO versus volume,
   68/70% coverage, tie-breaking POC, naked-level lifetime, break/re-entry confirmation, and exit
   logic are all strategy parameters.
8. **Overlap is high.** The proposal is another flexible level breakout/fade family adjacent to I-11,
   I-30, and the parked compression/zone ideas. It cannot serve as a same-data rescue layer.

## Decision and reopening condition

Park I-31. Do not infer volume-at-price from M1 time-at-price, do not use POC as a target, and do
not append value-area context to a failed setup.

Reconsider only if independent evidence freezes an OHLC-observable TPO construction and one side
before development, uses supported session/bin semantics, reports realistic net results across
multiple instruments and regimes with an untouched out-of-sample period, and shows incremental
value over simple prior-session range/location controls. No qualifying primary study was found in
this bounded check.
