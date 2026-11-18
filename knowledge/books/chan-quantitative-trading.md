# Ernest P. Chan, *Quantitative Trading: How to Build Your Own Algorithmic Trading Business*, second edition (Wiley, 2021)

Short: **QT**. Cite by printed page (`QT p.N`). Read 2026-11-18 by Codex; PDF in the library folder Tier 3.

The book introduces the process of finding, backtesting, executing, and managing quantitative trading strategies. Its examples cover equity mean reversion, pairs, seasonal effects, and futures, alongside practical issues such as transaction costs and data errors (QT pp.26, 58–59, 63–71, 174–186). The text extract does not visibly retain printed page numbers; the references below use the book’s index to locate the relevant sections.

## Testable ideas

- **Gasoline spring demand** (QT pp.183–185): Buy one May NYMEX RB gasoline futures contract at the April 13 close, or the following trading day if a holiday; sell at the April 25 close, or the previous trading day if a holiday. The claimed mechanism is demand ahead of the North American summer driving season. The book reports **19 profitable years out of 21 through 2015**, with 2007–2015 identified as out of sample, and provides annual dollar P&L per contract; **no basis-point size is given**. The accompanying claim of profit in every year since 1995 conflicts with the table’s losses in 2009 and 2012. Data needed: daily prices for the specified May contract, trading calendar, contract specifications, commissions and spread. Venue: exchange futures. **NEW**.

- **Post-earnings announcement drift** (QT p.136): Buy a stock when reported earnings exceed expectations and short when they fall short. The book attributes drift to gradual information diffusion or investors executing large orders incrementally. It does **not** specify a holding period, exit, surprise threshold, universe, effect size or sample in this discussion. Data needed: point-in-time earnings announcements and expectations, timestamps, and survivorship-aware daily share prices. Venue: real US shares. **NEW**.

- **Natural-gas spring demand** (QT pp.185–186): Buy a June NYMEX NG natural-gas futures contract at the February 25 close, or the following trading day if a holiday; exit at the April 15 close, or the previous trading day if a holiday. The claimed mechanism is anticipated summer demand from electricity generators serving air conditioning. The book tabulates annual dollar P&L for **1995–2016** and says the trade did not hold up as well out of sample; **no basis-point size is given**. Its prose and table differ on the stated consecutive profitable years and the beginning of the out-of-sample period. Data needed: daily June-contract prices, calendar, contract specifications, commissions and spread. Venue: exchange futures. **NEW**.

- **January small-cap tax-loss reversal** (QT pp.175–179): At the last December close, buy the prior-year bottom decile and short the top decile of S&P 600 stocks; exit at the last January close. The proposed mechanism is December tax-loss selling followed by relief from that pressure. The example reports portfolio returns of **−0.0244, −0.0068 and 0.0881** for January 2006, 2007 and 2008 respectively, with 5 bp one-way transaction costs in the code. Data needed: point-in-time small-cap membership and adjusted daily share prices. Venue: real US shares. **MAPS TO: month-end / turn-of-month**.

## Method notes

- Compare positions from a full-history run with those from a truncated-history run over their shared period; differences can expose lookahead (QT pp.58–59).
- Treat both parameter tuning and repeated qualitative choices—such as universe or entry time—as potential data snooping (QT pp.60–61).
- Use survivorship-aware equity data: omitted bankruptcies and acquisitions can particularly distort mean-reversion tests (QT pp.44–46).
- Check historical quotes for errors; a bad price followed by a corrected quote can create a fictitious mean-reversion profit (QT pp.134–135).
- Include commissions, spread, market impact and slippage when evaluating a strategy; attractive gross performance can disappear after costs (QT pp.25–26, 72–77).
- As a capacity heuristic, the author suggests limiting each equity order to 1% of average daily volume; this is a rule of thumb, not an execution guarantee (QT pp.101–102).
- For annual seasonal trades, the small number of independent events makes data snooping a concern; the author suggests examining nearby dates and seeking an economic rationale (QT pp.185–186).

## Verdict

The gasoline trade is the strongest **NEW** candidate for a research card: it has a specific contract and calendar rule, a demand rationale, and event-level dollar outcomes, including a marked out-of-sample period. Its stated mechanism is seasonal demand, though the book does not establish a counterparty compelled to trade, and it supplies no bp return; the contradictory prose also needs checking against the table. Natural gas has a similarly specific rule and dollar results but weak out-of-sample evidence. PEAD has a plausible execution mechanism but no stated size, sample, or complete trading rule here, so this book alone does not support a sized card.

Read selectively; no files changed. Tests were not run because this was a read-only book review. Open questions: the extract lacks visible printed page markers, so citations rely on the book’s index; the library PDF’s presence was not independently checked.