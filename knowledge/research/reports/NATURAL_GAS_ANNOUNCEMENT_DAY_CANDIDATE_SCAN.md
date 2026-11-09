# Natural-gas storage announcement-day candidate scan

Date: 2026-11-02  
Decision: **reject as a current candidate; the historical net-of-cost short disappears in the
authors' most recent subsample and a separate extended model finds no announcement-day mean**.

## Evidence

- Marcel Prokopczuk, Chardin Wese Simen, and Robert Wichmann, “The Natural Gas Announcement Day
  Puzzle,” *The Energy Journal* 42(2), 2021, 91–112,
  [accepted manuscript opened](https://doi.org/10.5547/01956574.42.2.mpro). The study uses 699
  scheduled releases and five-minute Henry Hub futures data from March 2003 through December 2018.
  A fixed short from 90 minutes before the 10:30 ET release until 30 minutes after earns an
  annualized 12%, t=2.93, and Sharpe 1.76 after the authors' transaction and funding costs. The
  return divides roughly equally before and after release and is not explained by the average
  storage surprise or controls.

  The same paper supplies the decisive rejection evidence. The effect is absent in its most recent
  2014–2018 subsample, after being stronger in 2003–2007 and 2007–2014. The authors state that the
  anomaly decreased and market efficiency appears to have returned. The pre-release component is
  also entirely generated on ex-post positive-surprise days, so surprise or season conditioning
  would not be a causal rescue available to an OHLC-only rule.

- Zhenhua Chen, “Temperature, Storage, and Natural Gas Futures Prices,” *Journal of Futures
  Markets* 43, 2023, [full text opened](https://doi.org/10.1002/fut.22402). In 3,005 trading days
  from January 2008 through December 2019, a model controlling for storage, temperature, oil, and
  financial variables estimates an announcement-day mean coefficient of −0.0033 with standard
  error 0.1412; it is removed from the reduced model as insignificant. This is not an intraday
  strategy replication, but it is independent contrary evidence against an unconditional modern
  announcement-day premium.

- U.S. Energy Information Administration, “EIA Information Releases,”
  [official page opened](https://ir.eia.gov/). The Weekly Natural Gas Storage Report is usually
  released Thursday at 10:30 ET and has a published holiday schedule. This establishes a scheduled
  event, not a stable return.

## Admission result

NATGAS is supported, the original rule is unambiguous and interior-session, its two-hour horizon is
compatible with M1 latency, and the authors explicitly include costs. It therefore passes more
admission gates than the other screened energy events. It fails the required modern-stability gate,
however, using the original authors' own predeclared late subsample and independent daily evidence.
Selecting the older era, injection season, extreme surprises, or a particular pre/post segment
would discard the adverse sample or condition on outcomes after seeing the decay.

Create no historical-era, season, surprise, pre/post-window, or holding-time grid. Reconsider only
after an independent modern study reports the same fixed intraday rule on a later untouched sample
with costs and a causal release calendar.
