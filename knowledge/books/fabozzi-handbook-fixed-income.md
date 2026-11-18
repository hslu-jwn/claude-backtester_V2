# Fabozzi, ed., *The Handbook of Fixed Income Securities*, Seventh Edition (McGraw-Hill, 2005)

Short: **HFIS**. Cite by printed page (`HFIS p.N`). Read 2026-11-18 by Codex; PDF in the library folder Tier 2.

This multiauthor handbook covers fixed-income instruments, markets, valuation, portfolio management and derivatives. The sections read describe how mortgage prepayment options change duration, how investors hedge that exposure, and how Treasury auctions and bond indexes operate (HFIS pp. 231–235, 573, 1020). It is primarily a practitioner reference: the passages examined explain the flows but do not establish their event-by-event trading profitability.

## Testable ideas

- **MBS convexity hedging after rate moves** (HFIS pp. 573, 1020): A manager maintaining stable mortgage-portfolio duration may add duration after rates fall and shed duration after rates rise. Banks may delta-hedge as mortgage duration changes, although the book does not say all banks do so. A possible *research hypothesis* is to follow this pressure in Treasury futures after a rate move; the book gives no entry threshold, execution time, exit, holding period or futures contract. **No effect size or event sample given.** Data needed: Treasury futures prices, an observable rate-move trigger and preferably contemporaneous estimates of MBS duration exposure; venue: exchange Treasury futures. **NEW.**

- **Treasury auction supply** (HFIS pp. 231–233, 1034): The Treasury sells a fixed announced amount through auctions, and the book describes primary dealers as expected to participate meaningfully. Auction cycles can also matter when selecting securities to replicate a government bond index. These facts motivate testing price behavior around issuance, but the book gives **no directional entry, exit, holding period, effect size or return sample**. Data needed: historical auction announcements, results and timestamps, plus matching Treasury futures or cash-bond prices; venue: exchange Treasury futures. **NEW.**

- **Bond-index replication and duration changes** (HFIS pp. 54, 1003, 1034): Bond index managers rebalance to match index composition, maturity and duration. The book also explains that matching callable-sector characteristics can reduce later trading as rates change. It does not quantify Treasury index-extension flow or give a dated trading rule, entry, exit, holding period, effect size or event sample. Data needed: historical index composition and duration changes, rebalancing dates and Treasury prices; venue: exchange Treasury futures. **MAPS TO: Treasury month-end duration.**

## Method notes

- A constant-duration MBS benchmark should bear hedging costs, including transaction costs and the cost of repeatedly adjusting after adverse price moves; otherwise comparison with a hedged manager is misleading (HFIS p.1020).
- A single duration measure captures sensitivity to a parallel yield-curve shift; key-rate durations help attribute exposure to different parts of the curve (HFIS p.1032).
- Matching only current convexity can leave a callable-bond portfolio needing costly rebalancing as rates change; the book suggests matching sector, coupon and maturity characteristics as well (HFIS p.1003).
- Benchmark replication is constrained by transaction costs: buying every constituent in exact proportions can require costly odd-lot trading (HFIS p.1034).
- Auction schedules and issue sizes changed with borrowing needs even during the book’s historical period, so historical event definitions should use the announcements for each event (HFIS pp. 234–235).

## Verdict

MBS convexity hedging and Treasury auction supply have identifiable counterparties and are **NEW** leads, but neither passage examined states a return size or a complete trade rule. Neither therefore meets the requested mechanism-and-size standard for a card yet. Index replication maps to the already-built Treasury month-end duration family; the book does not supply a separate quantified extension effect (HFIS pp. 54, 231–235, 573, 1020, 1034).

Read-only report: selectively inspected the contents and relevant passages. **Files changed:** none. **Tests:** not run; no code was changed. **Open questions:** none about trading rules; the missing effect sizes and trade specifications are evidence gaps.