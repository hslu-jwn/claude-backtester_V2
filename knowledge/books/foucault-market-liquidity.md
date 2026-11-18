# Foucault, Pagano and Röell, *Market Liquidity: Theory, Evidence, and Policy* (Oxford University Press, 2013)

Short: **ML**. Cite by printed page (`ML p.N`). Read 2026-11-18 by Codex; PDF in the library folder, Tier 2.

The book explains how trading mechanisms, order flow, dealer inventories and information affect liquidity and prices. It combines microstructure models with empirical evidence and discusses market design, liquidity crises and asset pricing. For this project, its strongest contribution is explaining why forced or unusually large orders can temporarily move prices—and why the resulting reversal need not be a profit available at quoted spreads. (ML pp.xii–xiii, 53–54, 116–118)

## Testable ideas

- **Mutual-fund redemption fire sales** (ML p.343): Funds facing large redemptions reduce positions, putting pressure on stocks held in common by distressed funds. A potential test would buy affected US shares after selling pressure becomes observable and exit after a specified recovery period. **The book does not give an exact entry, exit, holding period or effect size**, so these must be specified before testing; it cites Coval and Stafford’s evidence without reporting sample details here. Data: fund flows, point-in-time fund holdings and daily share prices; venue: real US shares. **NEW.**

- **Block-sale liquidity provision** (ML pp.6–7): Large sell orders can depress prices temporarily as counterparties absorb inventory; the book reports that the initial drop was largely, but not entirely, reversed before the subsequent market close. The cited sample is **7,009 block trades in 402 NYSE stocks, July 1, 1968 to September 30, 1969**; no numerical return size is given in the text reviewed. A possible test would buy after an identifiable block sale and exit by the subsequent close, but the book does not specify an executable entry or a complete trading rule. Data: timestamped block trades, trade direction, quotes and intraday prices; venue: real US shares. **NEW**, subject to distinguishing the block event from the already judged daily-reversal family.

- **Providing liquidity to market orders** (ML pp.53–54, 169–170): A liquidity supplier takes the other side of a market order, then unwinds later; the claimed compensation is reduced by adverse price movement after the fill. In a model-based example derived from Glosten and Harris’s NYSE estimates, a 1,000-share buy has a **5.67 cents per share** execution markup and **1.02 cents** permanent price impact, leaving **4.65 cents per share** expected realized spread. The cited study used transaction observations from December 1, 1981 to January 31, 1983 and a larger sample of 250 stocks; the book does not give a bp return or a complete executable quoting and exit rule. Data: trades, historical quotes, fill and queue assumptions, and fees; venue: real US shares. **NEW.**

- **Dealer-inventory pressure** (ML pp.116, 118): Dealers adjust prices to attract trades that reduce unwanted inventory; the inventory-related component should reverse as positions rebalance. For NYSE stocks, the cited estimate associates a **$1,000 inventory** with **1.01 basis points** of price pressure for small stocks and **0.02 basis points** for large stocks. These are pressure coefficients, not strategy returns; the book does not specify an entry, exit, sample period or tradeable inventory signal in the passage reviewed. Data: dealer inventories or a validated observable proxy, quotes and trades; venue: real US shares. **NEW.**

- **Downgrade-driven insurance fire sales** (ML p.343): Regulatory constraints and capital requirements can cause insurers to sell downgraded speculative-grade corporate bonds. The book reports price declines and subsequent reversals, particularly when insurers are distressed and other buyers have scarce capital; **no size given**. A test would buy exposed bonds after observable forced selling and exit on a predefined horizon, but the book supplies no exact rule or sample details in the passage reviewed. Data: bond downgrades, insurer holdings and constraints, transaction prices and point-in-time disclosure dates; the natural venue is corporate bonds, outside the project’s listed venues. **NEW**, but not an immediate fit.

- **Contrarian stock portfolio** (ML pp.336–337): Buy underperforming stocks and short outperforming stocks, holding for extended periods such as a month, on the premise that some moves reflect temporary liquidity shocks. The book gives no exact ranking, entry or exit rule and **no size given**. Data: daily US-share prices and shorting costs; venue: real US shares. **MAPS TO: daily reversal.**

## Method notes

- A quoted or effective spread can overstate a liquidity supplier’s gain because prices may continue moving against the supplier after execution. Measure the post-trade price movement as well as the initial execution price. (ML pp.53–54)
- The realized half-spread uses the transaction price and a later midpoint. Its interpretation assumes an unwind at that midpoint, so it is a markout measure rather than proof of an executable round-trip profit. (ML p.54)
- Choose and report the post-trade measurement interval: an interval that is too short misses quote adjustment; one that is too long introduces noise. (ML p.54)
- Inferring trade direction introduces classification errors; the book notes systematic problems for midpoint, small and frequently traded stocks. (ML p.52)
- Separate temporary inventory pressure from permanent information impact. A price move caused by information need not reverse, while inventory-related pressure may dissipate gradually. (ML pp.118, 176–177)
- Large-order economics can differ from average-trade economics: the cited estimates attribute a much larger share of the spread to inventory costs for large trades. (ML pp.174–175)
- Reversal speed and size are uncertain, and liquidity providers bear inventory and financing risk while waiting. (ML pp.336–337)

## Verdict

**Mutual-fund redemption fire sales** are the most promising new card: the book identifies a concrete forced seller and a venue the project can research, but it does **not state an effect size** in the passage reviewed. Block-sale and dealer-inventory pressure have relevant mechanisms; the former lacks a numerical return, while the latter’s bp figures are inventory-pressure estimates rather than achievable returns. The realized-spread example supplies a size in cents, but needs executable fills, costs and a complete rule before it can support a strategy card. None of these passages supplies both a complete trading rule and a stated bp-per-event return.

