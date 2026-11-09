# U.S. Treasury auction price-pressure candidate scan

Date: 2026-11-02  
Decision: **retain as promising but capability-blocked; do not proxy it through DXY or an equity
index and do not create a strategy specification**.

## Evidence

- Michael J. Fleming, Weiling Liu, and Giang Nguyen, “Intraday Price Pressure and Order Flow
  Around U.S. Treasury Auctions,” Federal Reserve Bank of New York Staff Report 1188, 2026,
  [full text opened](https://doi.org/10.59576/sr.1188). The study uses one-minute GovPX and
  BrokerTec data for nominal 2-, 3-, 5-, 7-, 10-, and 30-year on-the-run securities from June 1991
  through July 2024. Yields rise during the 180 minutes before the auction close and reverse during
  the 180 minutes after the result release. The result-time jump is excluded; a ten-minute buffer
  gives a similar result. Full-sample return pressure ranges from about 1.3 bp for the 2-year note
  to more than 13 bp for the 30-year bond. The effect is weaker after 2014 but remains statistically
  significant for the 3-, 5-, and 10-year notes. The paper estimates an issuance effect, not an
  executable strategy net of transaction costs.

- Dong Lou, Hongjun Yan, and Jinfan Zhang, “Anticipated and Repeated Shocks in Liquid Markets,”
  *Review of Financial Studies* 26(8), 2013, 1891–1912,
  [article record and abstract opened](https://doi.org/10.1093/rfs/hht034). Treasury prices fall
  before auctions and recover afterward over a multi-day auction cycle, consistent with limited
  dealer risk-bearing capacity. Its sample ends in 2008, so it establishes the prior mechanism but
  not modern stability or day-flat execution.

- Lee A. Smales, “The Effect of Treasury Auctions on 10-year Treasury Note Futures,” *Accounting
  & Finance* 61(S1), 2021, 1517–1555,
  [abstract opened](https://doi.org/10.1111/acfi.12635). In 15-minute futures data from 2000–2017,
  prices, volatility, and volume rise immediately after auctions. Stronger bid-to-cover ratios
  produce more positive returns, showing that result-conditioned direction depends partly on
  auction outcome data. The abstract does not report a net-of-cost rule.

## Admission result

The predictable supply event and the fixed pre-auction price decline/post-auction recovery are
economically identified and comfortably longer than one M1 bar. The latest study also separates
the inventory-pressure pattern from the auction-result information jump and retains evidence in a
2015–2024 subsample. This makes the territory stronger than a generic announcement response.

It nevertheless fails current admission. The canonical V2 universe contains no Treasury cash,
Treasury-futures, or bond-CFD instrument, and its cost tables therefore cannot establish executable
margin. The primary studies do not establish the same signed return in DXY, US500, NAS100, gold,
or another supported proxy. A Treasury auction calendar and its versioned historical timestamps
are also not part of the current shared contract. Substituting a supported macro proxy, selecting
a maturity after inspecting local returns, or conditioning on bid-to-cover/tail data would change
the published estimand and introduce unsupported inputs.

Create no proxy, maturity, auction-type, pre/post-window, or result-surprise grid. Reconsider only
if V2 gains a supported Treasury instrument with authoritative costs and a point-in-time auction
calendar. At that point, independently freeze one maturity and one side/window from the modern
evidence before any local outcome access.
