# I-43 M1 path-length activity-proxy method check

Date: 2026-10-29  
Decision: **volatility diagnostic only; never label it volume, absorption, or directional edge**.

## Question

Can the sum of M1 high-low ranges and the number of M1 direction changes inside a 5-minute to
1-hour bar stand in for market activity and validate “high activity plus small net range” absorption
or “wide range on low activity” directional moves?

## Evidence inspected

- Martin Martens and Dick van Dijk, “Measuring Volatility with the Realized Range,” *Journal of
  Econometrics* 138(1), 2007, 181–207,
  [DOI](https://doi.org/10.1016/j.jeconom.2006.05.019),
  [repository record](https://repub.eur.nl/pub/11121). **Repository abstract opened; full paper not
  opened.** Replacing squared intraday returns with normalized **squared log high-low ranges** can
  estimate realized volatility more efficiently, with explicit scaling and microstructure-bias
  correction. This supports range-based volatility measurement, not raw-range “activity” or volume.

- Kim Christensen and Mark Podolskij, “Realized Range-Based Estimation of Integrated Variance,”
  *Journal of Econometrics* 141(2), 2007, 323–349,
  [DOI](https://doi.org/10.1016/j.jeconom.2006.06.012). **Publisher abstract opened; full paper not
  opened.** It derives consistent realized-range variance estimators under specific normalization
  and corrects discrete-sampling/non-trading bias. Again, the estimand is quadratic variation.

- Giovanni Cespa, Antonio Gargano, Steven J. Riddiough, and Lucio Sarno, “Foreign Exchange Volume,”
  *Review of Financial Studies* 35(5), 2022,
  [DOI](https://doi.org/10.1093/rfs/hhab095),
  [accepted-version record](https://www.repository.cam.ac.uk/items/6125f8ba-42ba-433a-8327-11c1b71e6729).
  **Abstract and repository record opened; full accepted paper not opened.** Actual OTC FX volume
  contains predictive information even after separating components related to volatility,
  illiquidity, and order flow. This distinction directly contradicts treating price-path volatility
  as volume.

- Menkhoff and Schlumberger-era Reuters evidence summarized in “Do Reuters Spreads Reflect
  Currencies' Differences in Global Trading Activity?”, *Journal of International Money and Finance*,
  1999, [publisher page](https://www.sciencedirect.com/science/article/abs/pii/S0261560698000242).
  **Publisher abstract/extended summary opened; full paper not opened.** Reuters tick frequency is
  an imprecise high-frequency activity proxy and its relationship with actual turnover is unstable,
  even when monthly aggregation can correlate. A broker-specific count therefore requires direct
  validation before it can approximate market-wide activity.

## What the proposed variables actually measure

- A properly normalized sum of squared log M1 ranges can be a **realized-volatility estimator**.
- A raw sum of price-unit ranges is scale-dependent and not the established realized-range
  estimator. Comparing gold, FX, and indices without log/volatility normalization is invalid.
- Direction-change counts depend on bar construction, zero returns, spread bounce, price precision,
  missing bars, and the chosen sign/tie rule. They measure observed path roughness, not orders.
- Neither statistic measures executed volume, aggressive/passive side, depth, replenishment, or
  absorption. The same small net move and large path can arise from information arrival, quote
  bounce, alternating liquidity, or a transient data artifact.

## Multiplicity and causal constraints

“High,” “small,” “swing extreme,” and “wide on low activity” require thresholds, normalization,
clock-time controls, lookbacks, and direction rules. Searching their combinations would create a new
technical-rule family while presenting it as a measurement exercise.

If the statistic is ever reported, it must be frozen as a descriptive volatility/path diagnostic:

1. use causal prior-data normalization per symbol and clock bucket;
2. publish the exact squared-log realized-range formula separately from raw exploratory measures;
3. specify missing/flat M1 bars and direction-change ties;
4. compare it with simple realized variance/range and available broker tick volume;
5. report correlations and stability by year/session, not trade P&L; and
6. prohibit it from reversing an unconditional strategy decision.

## Decision

Do not create an I-43 strategy, absorption signal, volume filter, or directional trial. The only
admissible future use is method validation as a volatility/path diagnostic. Promoting it would require
independent data showing stable correlation with the intended market-wide activity variable at the
same symbol, feed, and horizon, followed by separately preregistered evidence that it adds net
directional value. No such evidence was found.
