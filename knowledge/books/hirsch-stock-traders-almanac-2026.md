# Jeffrey A. Hirsch and Christopher Mistal, *Stock Trader’s Almanac 2026*, 59th edition (John Wiley & Sons, 2026)

Short: **STA**. Cite by printed page (`STA p.N`). Read 2026-11-18 by Codex; PDF in the library folder Tier 3.

The Almanac surveys historical US equity-market seasonality, election cycles, sector patterns and trading calendars. Its evidence is principally descriptive historical averages and date-based patterns, with some proposed trading rules and explanations for flows. Many of its patterns overlap families already judged in this project.

## Testable ideas

- **Year-end tax-loss losers** (STA p.116): The original study buys NYSE stocks making new lows on December 15 and holds until February 15, excluding preferred shares, closed-end funds, splits and new issues. The proposed mechanism is investors selling losers for tax purposes, temporarily depressing prices. The book reports a **51-year average return of 10.6% versus 3.2% for the NYSE Composite**, an average advantage of **7.4 percentage points**. The series is heterogeneous: from December 1999 onward it uses an actual newsletter portfolio, adds NASDAQ and AMEX selections, and sometimes sells sooner. The current rule instead compiles new lows on the triple-witching Friday before Christmas, removes problematic names judgmentally and sells quick gains; its exact entry and exit are therefore not fully mechanical. Data: point-in-time daily US share prices, 52-week lows, corporate actions, delistings and trading costs. Venue: real US shares. **NEW**.

- **Small-cap year-end relative strength** (STA p.112): Buy a Russell 2000 exposure at the close of the 11th December trading day and exit at December’s close; compare it with the Russell 1000. The book links the effect to tax-loss selling in beaten-down small shares. In its **38-year sample, December 1987–February 2025**, it reports average December 15–31 returns of **2.5% for Russell 2000 and 1.3% for Russell 1000**. A long-small/short-large implementation and its costs are not stated. Data: daily index or ETF prices and financing costs. Venue: US equity ETFs or index futures. **NEW**, but related to the tax-loss idea above rather than independent evidence.

- **Sector seasonal windows** (STA p.94): The book lists, for example, long natural-gas equities from the end of February to the beginning of June, reporting average returns of **16.19%, 17.82% and 22.56%** over its 25-, 10- and 5-year windows, respectively. “Beginning,” “middle” and “end” mean thirds of a month, so exact execution dates are unspecified. The book gives no specific counterparty or flow mechanism for this window. Data: point-in-time sector index or ETF daily prices and costs. Venue: US sector ETFs. **NEW**, but a calendar pattern without the requested mechanism.

- **Best six months** (STA p.54): Invest in the Dow from November 1 through April 30, switching to fixed income for May–October. The book reports **29,918.50 Dow points** gained in November–April versus **10,536.53 points** in May–October over 75 years; these are aggregate index points, not bp per event. It does not establish a specific forced counterparty for the rule. Data: daily index or ETF prices and fixed-income returns. Venue: US equity ETFs or index futures. **NEW**, though the book’s presentation is a broad seasonal allocation rather than a clearly identified flow.

- **Down Friday/down Monday warning** (STA p.78): Flag a Dow decline on the last trading day of a week followed by a decline on the first trading day of the next. The book attributes Friday positioning partly to traders reducing weekend exposure, but gives a warning to examine conditions rather than a mechanical entry or exit. It reports **302 occurrences since 1995**, including **92** in its listed bear-market years; no executable per-event return is given. Data: daily Dow prices. Venue: index futures or CFDs. **MAPS TO: day-of-week**.

- **Monthly cash inflows** (STA p.147): The book associates strength around month boundaries with investment inflows and suggests twice-monthly salaries and retirement contributions may explain a mid-month bulge. It describes the ninth through twelfth trading days but specifies no complete trading rule or return size for that window. Data: daily S&P 500 prices and, for mechanism validation, contribution-flow data. Venue: US index futures or ETFs. **MAPS TO: month-end / turn-of-month** for the month-boundary claim; the mid-month explanation remains a hypothesis with no size given.

## Method notes

- The tax-loss study changes universe and exit practice partway through its history; its aggregate average should not be treated as the result of one unchanged mechanical rule. Reconstruct each period separately before comparing results. (STA p.116)
- The book says its tax-loss portfolio has worked better after corrections and when more new lows were available. Those conditions are retrospective observations unless defined before testing. (STA p.116)
- The small-cap table defines mid-month as the **11th trading day** and month-end as the **monthly close**, rather than always using the literal dates in the table headings. (STA p.112)
- Sector entries and exits are specified only to a third of a month; a reproducible test must choose dates without optimizing against the same reported sample. (STA p.94)
- The book describes historical monthly inflow patterns shifting over time and suggests traders anticipated them. Stability and costs therefore matter when evaluating calendar effects. (STA p.147)
- Its intraday discussion reports how often the Dow rose over preceding half-hour periods, rather than a net return after costs; frequency alone does not establish a tradable edge. (STA pp.140–142)

## Verdict

The **year-end tax-loss loser basket** is the strongest candidate for a research card: the book supplies an identifiable selling motive, a defined historical holding period and a substantial stated average advantage. Its changing portfolio rules, discretionary filtering and likely costs make that figure unsuitable as a clean estimate of a reproducible edge. Small-cap year-end strength also has a stated size and a related tax-selling explanation, but is less directly tied to the affected shares. Sector windows and the best-six-months allocation have reported historical performance but lack a sufficiently specific forced-flow mechanism; the warning and monthly-flow observations do not add a complete, sized new rule.

