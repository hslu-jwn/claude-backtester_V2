# London gold benchmark candidate scan

Date: 2026-11-02  
Decision: **reject; the source-matched edge was a four-minute leak in the pre-2015 private fixing,
requires contemporaneous trade information, and does not transfer to the reformed benchmark**.

## Primary evidence

- Andrew Caminschi and Richard Heaney, “Fixing a Leaky Fixing: Short-Term Market Reactions to the
  London PM Gold Price Fixing,” *Journal of Futures Markets* 34(11), 2014, 1003–1039,
  [abstract opened](https://doi.org/10.1002/fut.21636). GC futures and GLD volume/volatility rose
  immediately after the old fixing began, before its result was public. Trades in the opening
  minutes predicted the fixing direction, sometimes above 90%, and informed traders had a
  significant advantage during the next four minutes. No significant return followed publication.
  The signal is therefore leaked contemporaneous trade direction with sub-five-minute latency, not
  a predetermined long/short calendar rule.

- Susan J. Crain, Seth A. Hoelscher, and Jeffrey S. Jones, “Fixing the Fix for Silver and Gold,”
  *ACRN Journal of Finance and Risk Perspectives* 9(1), 2020, 177–197,
  [full-text record opened](https://doi.org/10.35944/jofrp.2020.9.1.013). The study compares the old
  opaque dealer process with the electronic auction introduced for gold in 2015 and finds material
  changes in precious-metals prices and volatility. It does not establish a fixed post-reform
  directional strategy net of executable costs.

- UK Financial Conduct Authority, “The Impact of Bringing Additional Benchmarks into the
  Regulatory and Supervisory Regime,” Evaluation Paper 18/2, 2018,
  [official paper opened](https://www.fca.org.uk/publication/corporate/evaluation-paper-18-2-the-impact-of-bringing-additional-benchmarks-into-the-regulatory-and-supervisory-regime.pdf).
  Market participants associated the electronic gold/silver auction with greater transparency and
  lower manipulation risk. The institutional mechanism studied in the old leak paper is therefore
  not stable across the current benchmark regime.

## Admission result

The event occurs at an interior London time and XAUUSD is supported, but the estimand overlaps the
already counted benchmark-fix leakage/reversal family. The only claimed economic return lasts four
minutes, uses trade information unavailable in OHLC-only input, and predates the 2015 auction
reform. Waiting for a completed M1 bar consumes a material fraction of the horizon; using its close
as an earlier fill would be lookahead. Neither the reform study nor official evaluation supplies a
modern unconditional sign or cost-adjusted strategy. Searching AM versus PM, pre/post windows,
breakouts, or reversal horizons would be a new grid around a failed fix family.

Create no gold-fix draft, AM/PM comparison, leak proxy, or reversal grid. Reconsider only with an
independent post-reform primary study that uses causal supported inputs, a response comfortably
longer than M1 latency, a fixed direction, and executable net costs.
