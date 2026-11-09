# I-11 midday support/resistance and afternoon-breakout evidence check

Date: 2026-10-29  
Decision: **park; source result does not identify the frozen day-flat adaptation**.

## Question

Does the cited result support a day-flat S&P/index rule that defines the morning range through noon,
fades closes in its outer quartiles, reverses on later range breaks, and exits at the close?

## Source inspected

- Perry J. Kaufman, *Trading Systems and Methods*, 5th ed., Wiley, 2013, Chapter 16,
  “TSM Midday Support and Resistance,” pp. 754–755,
  [publisher page](https://www.wiley.com/en-it/trading-systems-and-methods-5th-edition-p-9781119202561),
  [relevant page scan](https://www.yumpu.com/en/document/view/63114029/trading-systems-and-methods-2013/774).
  **Relevant book pages opened.** The book reports $268 per trade before costs over 8,404 S&P
  futures trades from January 2000 to mid-May 2011 using 15- or 30-minute bars, noon, and 25%
  trigger zones. It says the midday time and trigger zone were not tuned and describes the result as
  an illustration of turning a trading principle into a strategy, not an independent replication.

- Perry J. Kaufman companion-code inventory, “Trading Systems and Methods,”
  [public mirror](https://github.com/liujiantong/TSM). **Repository inventory opened.** It confirms
  that a TradeStation strategy named `TSM Midday Support and Resistance` existed, but the public
  mirror contains only an inventory/readme, not the code, data, contract-roll settings, or result
  reproduction needed for an audit.

No independent peer-reviewed or institutional reproduction of the exact rule was found in the
bounded search.

## Material mismatch with I-11

The source immediately states that trades **can be held into the next day** and that doing so can
greatly increase profit per trade. It does not make clear on the inspected result page whether the
$268 figure uses forced close, overnight carry, or a platform session default. The frozen backlog
instead says “exit at the close.” Because the result cannot be allocated between intraday and
overnight P&L, it is not evidence for the day-flat version.

Other unresolved items are also decision-relevant:

1. **Costs are absent.** The $268 is gross and the strategy can reverse repeatedly. Commissions,
   bid/ask spread, slippage at range breaks, and continuous-contract roll treatment are not reported.
2. **Execution semantics are missing.** The prose mixes bar-close quartile signals with “prices
   break” the range. Same-bar ordering, next-bar entry, session timestamps, and close liquidation are
   not specified well enough to prevent optimistic fills.
3. **The sample is one market and one era.** S&P futures from 2000–2011 include pit/electronic and
   contract changes. There is no untouched out-of-sample period, cross-instrument confirmation, or
   regime stability table.
4. **Trade count is unusually high for one afternoon position per day.** 8,404 trades across roughly
   11.4 years implies multiple counted entries/reversals on many days. The result may therefore mix
   the fade and breakout mechanisms and exposes substantial turnover.
5. **The rule is a state machine, not one hypothesis.** It combines lower-quartile long, upper-
   quartile short, upside breakout reversal, and downside breakout reversal. Aggregate profit cannot
   show which component earns the return or whether one offsets another.
6. **“No tuning” is not independent selection control.** Noon, quartiles, S&P, bar length, and the
   combined rule may still have been selected from practitioner experience; the book provides no
   search accounting or pre-registration.
7. **Local overlap is substantial.** Morning-range boundaries, reversals, breakouts, and close exits
   overlap opening-range and intraday level families already tested or parked. A new implementation
   would expand the same broad family rather than supply independent validation.

## Decision and reopening condition

Keep I-11 parked. Do not infer that the reported gross result survives a day-flat close, and do not
split the four components into a development-data search.

Reconsider only if the original code/result accounting or an independent reproduction establishes:

- forced same-session liquidation and exact session/bar timestamps;
- causal next-bar execution and same-bar reversal ordering;
- component-level trades and P&L, contract-roll handling, and realistic costs/slippage;
- stability across subperiods and at least one untouched market or later sample; and
- a frozen small rule surface that counts the fade and breakout components separately.

Without those items, the $268 gross figure is a research lead, not a submit-ready day-flat edge.
