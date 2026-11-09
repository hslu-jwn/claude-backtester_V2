# I-13 Nofri congestion third-bar reversal evidence check

Date: 2026-10-29  
Decision: **reject as a research candidate; retain the negative replication**.

## Question

Does independent evidence support adapting Nofri's daily congestion-phase reversal to a high-
frequency, day-flat OHLC rule with an added ATR stop?

## Sources inspected

- Eugene Nofri and Jeanette Nofri Steinberg, *Success in Commodities: The Congestion Phase
  System*, 1975, [National Agricultural Library record](https://agris.fao.org/search/en/providers/122535/records/65ddd5f30f3e94b9e5c5a20f).
  **Bibliographic record opened; original book not opened.** The claimed method is a daily
  commodity chart system with 32 patterns and a reported roughly 75% winning rate. This is not an
  intraday sample and the original full rule set was not available for audit.

- Fred Gehm, “Two Steps Forward and One Step Back: The Congestion Phase Charting System,”
  *Market Technicians Association Journal*, Fall 1991, 22–27,
  [full issue/text opened](https://www.scribd.com/document/582750494/38-1991-Fall).
  **Full article opened.** Gehm states that the original method is too vague and rule-heavy to test
  as written, then programs three explicit adaptations and the two basic two-day reversal patterns.
  It tests continuous daily series for wheat (April 1968–December 1988), gold (December
  1974–December 1988), and S&P 500 (April 1982–December 1988), producing 3,825 trades.
  Neither equal- nor unequal-variance t-tests distinguish returns after long and short signals.
  S&P long and short signals both lose; wheat and gold short signals profit but buy signals lose.
  The paper concludes the presented system does not work and sees little hope from the tested
  evidence. Costs are not needed to reverse that gross null/adverse verdict.

- Perry J. Kaufman, *Trading Systems and Methods*, discussion of “Nofri's Congestion-Phase
  System,” [relevant text opened](https://studylib.net/doc/28083837/trading-systems-and-methods-wiley-trading-compress).
  The book describes the daily third-bar reversal and reports that performance was good for a long
  period in some markets but suffered large losses during the 2008 crisis. It presents a wheat chart,
  not a documented cross-market, cost-aware result table for the proposed intraday adaptation.

## Why I-13 is rejected

1. **There is a direct negative replication.** A mechanically explicit version across three long
   daily series and 3,825 trades finds no significant directional separation and loses on both S&P
   sides. That is stronger evidence than the original unverified win-rate claim.
2. **The adaptation changes the horizon.** The source system uses daily closes and next-day exits.
   Moving it to intraday bars changes participant behavior, serial dependence, spread burden, and
   the meaning of a congestion phase.
3. **The original pattern family is not reproducible.** Thirty-two patterns include qualitative
   distinctions such as “large” versus “small” moves. The independent reviewer had to alter rules
   before programming them.
4. **The 75% runs argument is invalid.** After observing two moves in the same direction, an
   independent fair-sign process still has a 50% probability for the next sign; multiplying
   unconditional path probabilities does not imply a 75% conditional reversal probability.
5. **The frozen version adds further searches.** Bar timeframe, range construction, large-move
   pause, false-break pause, profit re-evaluation, range exit, and ATR stop all create parameters
   absent from independently positive evidence.
6. **Turnover attacks the premise.** The idea anticipates many small trades. Even a weak gross
   effect would face spread and slippage repeatedly, while the direct replication is already null
   before costs.
7. **A volatility filter would be a rescue search.** Crisis losses or trend regimes do not authorize
   adding an ex-post ATR/volatility gate to discover a surviving subset.

## Decision

Do not draft or test I-13, and do not reinterpret the negative replication as evidence that only an
intraday version remains promising. A future reconsideration would require a new independent,
predefined intraday study with exact congestion state, next-bar execution, realistic costs, multiple
markets/regimes, and untouched out-of-sample confirmation. No such evidence was found.
