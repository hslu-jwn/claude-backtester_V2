# Richard Grinold and Ronald Kahn, *Advances in Active Portfolio Management* (McGraw-Hill Education, 2020)

Short: **AAPM**. Read 2026-11-18 by Codex; PDF in the library folder Tier 3, as identified in the brief.

The book collects research on quantitative active portfolio management, with particular emphasis on changing forecasts, trading costs, portfolio attribution, factor exposure and diversification. Its central concern is translating investment forecasts into portfolios and evaluating their risks and implementation. (AAPM p.124–125, p.170–172, p.512–516)

The supplied text is a reflowable ebook extraction: its page breaks do not retain printed page numbers. The references below use the book’s printed-page **index** to locate the relevant topics; where the index gives a range, I cite that range rather than inventing a precise page.

## Testable ideas

No new event-driven trading idea met the brief’s standard of a specified trade, a forced-counterparty mechanism and a stated return size.

- **Cost-aware adjustment toward a target portfolio** (AAPM p.143, p.170–172): Construct a target from investment signals and trade a fraction of the difference between current holdings and the target at each rebalance. The book models slower adjustment when trading costs are higher. It does not give a universal entry, exit, holding period or universe, and gives **no empirical return size** for this rule. Testing would require timestamped target positions, holdings, prices and venue-specific costs; it could apply to real US shares or futures. **NEW**, as an implementation method, but not as a standalone trading effect.

## Method notes

- Estimate a signal’s information decay and distinguish it from how quickly the portfolio trades toward its target. Fast-decaying signals and high costs create different implementation demands. (AAPM p.63, p.132, p.143)
- Compare an ideal forecast portfolio with actual holdings: a persistent gap can sacrifice forecast value even before explicit trading costs are deducted. Evaluate the trade-off after costs. (AAPM p.125–129, p.131–137)
- When combining signals, account for their correlations and different decay rates; combine source portfolios into a target, then specify how the actual portfolio approaches it. (AAPM p.170–172, p.177–180)
- Diversifying across strategies can leave the combined portfolio concentrated in shared factor risks. Inspect exposures and correlations at the portfolio level, including crisis periods, rather than relying only on individual strategy risk. (AAPM p.512–516)
- Distinguish theoretical factor portfolios from investable portfolios: the book’s illustrative characteristic portfolios disregard liquidity, borrowing availability and transaction and borrowing costs. (AAPM p.432–434)

## Verdict

The **NEW** cost-aware adjustment rule is useful as a portfolio implementation research card, but it lacks the required observed return size and forced-counterparty mechanism for an effect card. The book’s principal value for this project is in testing how signal decay, costs and shared exposures affect a portfolio of already-researched strategies.

