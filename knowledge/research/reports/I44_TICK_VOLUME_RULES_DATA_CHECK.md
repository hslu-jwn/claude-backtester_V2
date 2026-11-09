# I-44 tick-volume rules data and evidence check

Date: 2026-10-29  
Decision: **blocked; do not approximate executed volume, true VWAP, or absorption from OHLC/path
variables**.

## Question

Can broker tick volume validate high-volume breakouts, climax/test bars, absorption, or true VWAP in
the current research interface?

## Evidence inspected

- Giovanni Cespa, Antonio Gargano, Steven J. Riddiough, and Lucio Sarno, “Foreign Exchange Volume,”
  *Review of Financial Studies* 35(5), 2022,
  [DOI](https://doi.org/10.1093/rfs/hhab095),
  [accepted-version record](https://www.repository.cam.ac.uk/items/6125f8ba-42ba-433a-8327-11c1b71e6729).
  **Abstract/repository record opened; full paper not opened.** Actual OTC volume contains return
  information distinct from volatility, illiquidity, and order flow. The result supports studying
  real volume; it also shows why price volatility is not a substitute.

- “Do Reuters Spreads Reflect Currencies' Differences in Global Trading Activity?”, *Journal of
  International Money and Finance*, 1999,
  [publisher page](https://www.sciencedirect.com/science/article/abs/pii/S0261560698000242).
  **Publisher abstract/extended summary opened; full paper not opened.** Reuters quote-update
  frequency correlates with turnover at monthly horizons in its sample, but the relationship is
  unstable and tick frequency is imprecise for high-frequency estimation.

- Caspar Marney, “Are Price Updates a Good Proxy for Actual Traded Volume in FX?”, *FX Trader
  Magazine*, 2011, [full article](https://varianse.com/wp-content/uploads/2022/07/fxvolume-tick-volume-vs-real-volume-study-1.pdf).
  **Full practitioner article opened.** Hourly tick counts for four major FX pairs correlate highly
  with EBS/HotSpot volume during a short 2010–2011 sample. This is encouraging for feed-specific
  hourly validation, but it is not peer-reviewed, does not establish bar-level trade direction or
  absorption, and cannot be assumed for a different broker, era, or non-FX symbol.

## Data-semantic limits

1. **Broker tick volume counts updates, not contracts or notional.** It is venue/feed specific in a
   fragmented OTC market and can change with aggregation, throttling, precision, and quoting policy.
2. **True VWAP requires executed price-volume pairs.** OHLC plus update counts cannot reconstruct
   which price carried which executed quantity. A tick-count-weighted typical price is not VWAP.
3. **Absorption requires side/depth information.** High update count with a small bar does not reveal
   aggressive buying versus selling, passive replenishment, cancellations, or quote bounce.
4. **Relative volume needs clock normalization.** FX and index activity have strong intraday and DST
   patterns. A rolling all-hours quantile confounds time of day with abnormal activity.
5. **The proposed A/B is not one test.** Breakout confirmation, climax reversal, low-volume test,
   true VWAP, quantile, lookback, rising-volume definition, and symbol/timeframe create distinct
   hypotheses and must not be bundled.

## Required unblock gate

I-44 remains blocked until a canonical, supported field has documented semantics and coverage. Before
any strategy trial, a research-only data study must freeze and report:

- field definition, source, update aggregation, missing/zero behavior, and historical availability;
- per-symbol/session coverage, DST alignment, distribution, and structural breaks;
- causal per-clock normalization and stability by year;
- for any “volume” claim, correlation against an authoritative executed-volume sample at the same
  horizon where legally and operationally available; and
- explicit labels: `broker_tick_activity`, never `executed_volume`, `order_flow`, or `absorption`.

Only after that gate may one externally supported, preregistered A/B be considered. It must compare a
fixed price-only rule with exactly one tick-activity interaction and count both trials. Passing the
data gate establishes measurement fitness, not directional edge.

## Decision

Do not draft or queue any I-44 rule and do not synthesize tick volume from M1 path length. True VWAP
and absorption remain unsupported with current data. No result from I-43 or I-38 changes this block.

Implementation follow-up 2026-11-03: `I44_V2_TICK_ACTIVITY_FIELD_AUDIT.md` traces V2's field.
MT5 update counts exist, but are duplicated into bid/ask volume, lose source identity, and all-NaN
histdata groups become zero during resampling. The required measurement declaration must preserve
unknown separately from observed zero before the coverage/stability/proxy gate can begin.

The research-only synthetic declaration and validator now encode that prerequisite. They require
single-feed complete coverage, immutable source/snapshot identities, same-clock normalization,
clock/calendar links, structural-break diagnostics, and the label `broker_tick_activity`, while
forbidding claims of executed volume, VWAP, order flow, absorption, or trade direction. Passing
the synthetic tests is not evidence that any real interval is supported.
