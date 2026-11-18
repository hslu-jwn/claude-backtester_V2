# Perry Mehrling, *The New Lombard Street: How the Fed Became the Dealer of Last Resort* (Princeton University Press, 2011)

Short: **NLS**. Cite by printed page (`NLS p.N`). Read 2026-11-18 by Codex; PDF in the library folder Tier 2.

The book explains the modern money market through the balance sheets of banks, securities dealers and the Federal Reserve. It traces how dealers finance securities inventories with short-term borrowing, how a funding squeeze can force asset sales, and how the Fed responded to the 2007–08 crisis as a lender and dealer of last resort (NLS pp.23–27, 98–107, 119–125). Its emphasis is institutional mechanics, not tested trading strategies.

## Testable ideas

The book does **not** specify complete entry and exit rules for the ideas below. The proposed tests are research interpretations of its mechanisms, not rules or measured trading returns from the book.

- **Money-market funding stress and liquid asset prices** (NLS pp.96, 100, 105–106): Test whether unusually wide money-market funding spreads precede weaker prices for assets held by leveraged dealers. A possible implementation would observe the spread at the close and enter a supported futures or CFD position on the next session; entry threshold, direction by instrument, exit and holding period would need a research spec. **Mechanism:** borrowers without eligible collateral or access to federal funds must bid up alternative funding rates; falling collateral values can also force dealers to liquidate inventories. **Size and sample:** the book says the spreads were normally “a few basis points” and reached “100 basis points or more” during the crisis; it gives no systematic sample or asset-return size. These are funding-rate spreads, not returns per trade. **Data:** historical repo, federal funds and Eurodollar rates, plus daily instrument prices and costs. **Venue:** exchange futures or FTMO CFDs, subject to an instrument-specific cost model. **NEW.**

- **Dealer funding relief and Treasury prices** (NLS pp.101–102): Test the response of Treasury futures to changes in dealer funding availability. The book describes expansionary Fed repo lending increasing funds available to dealers, which can encourage larger long-bond inventories and higher quoted bond prices. It gives no executable entry, exit, holding period or quantified return; these must be specified separately, including how an observable funding operation is identified before entry. **Size and sample:** no size given; the discussion is stylized rather than a reported event study. **Data:** historical Fed repo operations and timing, Treasury futures prices, and futures costs. **Venue:** exchange futures. **NEW.**

- **Funding squeeze and less-liquid securities** (NLS pp.105–106): Test whether a funding shock produces larger price declines in less-liquid securities than in liquid Treasury securities. The book’s mechanism is that dealers require a price concession to absorb selling, and assets without a reliable two-way market or eligible central-bank collateral can require a larger concession. It specifies no security universe, signal threshold, entry, exit or holding period. **Size and sample:** no measured return size or sample given; the book’s illustrative statement that an exotic security’s yield spread might be only a few basis points in good times is not an estimated trading effect. **Data:** point-in-time liquidity measures, funding rates, security prices and executable costs. **Venue:** potentially real US shares or exchange futures, if the selected instruments actually represent the mechanism; the book’s example concerns securities relative to Treasuries. **NEW.**

## Method notes

- Model collateral value and funding availability together: a falling asset price can reduce borrowing capacity and prompt liquidation before an institution is technically insolvent (NLS pp.100, 106).
- Distinguish **funding liquidity** from **market liquidity**. Stable funding in one part of the system does not guarantee a liquid market for every asset (NLS pp.98–99, 105–106).
- Account for dealer balance-sheet capacity: expected profit is weighed against liquidity risk, and constrained dealers may change the prices at which they quote (NLS pp.100–102).
- Treat central-bank intervention as part of the regime. The book describes successive facilities and changes in eligible counterparties and collateral during 2007–08, which could change the relationship being tested (NLS pp.119–121).
- Avoid treating a funding-rate spread as an asset return. The book reports crisis spread levels but does not establish the profit of an entry-and-exit strategy based on them (NLS p.96).
- Consider the asymmetry between collateral types: the book describes haircuts rising particularly sharply for non-Treasury securities during the crisis (NLS p.27).

## Verdict

None of the NEW ideas has **both a stated asset-return size and a sufficiently specified rule** to merit a strategy card under the requested standard. Money-market spread stress is the strongest lead: the book supplies a forced-funding mechanism and a stated rate-spread magnitude, but no per-event asset return, systematic sample or holding rule (NLS pp.96, 100). The other two are useful mechanism hypotheses with no measured effect size (NLS pp.101–102, 105–106). I found no specified funding-stress calendar with a measured trading effect in the relevant sections.

