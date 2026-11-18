# Harvey, Ramachandran and Santoro, *DeFi and the Future of Finance* (Wiley, 2021)

Short: **DEFI**. Cite by printed page (`DEFI p.N`). Read 2026-11-18 by Codex; PDF in the library folder Tier 3.

The book explains the infrastructure and incentives behind decentralized finance, then describes lending, decentralized exchanges, derivatives and tokenized portfolios (DEFI pp.18–29, 69–130). Its most relevant mechanisms are collateral liquidation, automated market maker pricing and arbitrage (DEFI pp.48, 51–54, 71–75, 98–102). The numerical trading examples are illustrations, not measured samples of strategy returns (DEFI pp.71–72, 101–102, 112–113).

## Testable ideas

- **Collateral-liquidation selling** (DEFI pp.71–72, 75): When an ETH-backed loan falls below its collateral ratio, a keeper can trigger an auction selling collateral to repay DAI debt. The book’s illustration starts with 5 ETH, 500 DAI debt and a 150% threshold; at ETH $150 it describes selling 3.33 ETH and paying the keeper 0.2 ETH. **No measured effect size or sample given.** The book does not specify a price-trading entry, exit or holding period. Testing a Binance ETH futures response would need timestamped vault positions, oracle prices, liquidation and auction events, and contemporaneous execution prices. **NEW.**

- **AMM cross-venue price correction** (DEFI pp.98–102): Buy the cheaper asset on one decentralized exchange and exchange it on another, closing both legs in one transaction when proceeds exceed repayment and costs. The counterparty is an AMM whose pricing curve changes with its asset balances; arbitrage moves its price toward the wider market. In a hypothetical USDC/DAI flash swap, the book illustrates **37 DAI profit** on 950 USDC borrowed, after illustrated pool slippage and a 3 DAI fee; it gives no empirical sample and does not include gas in that calculation. Testing requires transaction-level pool reserves, executable prices, fees, gas and ordering data. The described venue is on-chain DEXs, rather than the project’s listed venues. **NEW.**

- **Redeemable stablecoin dislocation** (DEFI p.77): The book describes buying USDC below $1 and redeeming it for $1, or selling at a premium elsewhere with the corresponding issuance/redemption route. The claimed anchor is redemption with Coinbase, conditional on its solvency. The book gives **no observed spread, holding time, effect size or sample**, and does not provide a complete executable premium-side procedure. Testing needs timestamped executable USDC/USD quotes, historical creation and redemption terms, fees and settlement delays. The described venue is stablecoin spot and redemption, outside the listed project venues. **NEW.**

- **Subsidized borrowing from token distributions** (DEFI pp.86–87): Supply or borrow on Compound when the value of distributed COMP exceeds the relevant borrowing and transaction costs; close when the subsidy no longer covers costs. The mechanism is governance-token distribution to suppliers and borrowers. The book says borrowing in most markets became profitable after the 2020 distribution, but gives **no measured net return, duration or sample**. Testing requires historical rates, reward allocations, COMP prices, gas and liquidation costs. The described venue is on-chain lending. **NEW.**

- **Dynamic Set moving-average allocation** (DEFI p.125): A Set shifts between 100% ETH and 100% USDC when ETH crosses its configured moving average. The book gives no particular average length, execution delay, return size or sample. **MAPS TO: diversified or single-symbol trend following at any speed.**

## Method notes

- A collateral threshold can be reached without a grace period; historical tests of liquidation-driven flow need the relevant oracle and protocol rules at the time, rather than assuming a discretionary margin-call delay (DEFI pp.71, 75).
- AMM execution depends on pool depth and trade size. The book’s 4 DAI example receives 2 USDC from a 4/4 pool versus 3.85 USDC from a 100/100 pool; these are illustrations of slippage, not observed trades (DEFI pp.96–97).
- Liquidity-provider fees must be compared with the opportunity cost of holding the assets directly, including impermanent loss as relative prices move (DEFI pp.52–54, 98).
- Public pending transactions can expose large, illiquid AMM trades to transaction ordering and front-running; a maximum-slippage setting limits execution price but does not eliminate that exposure (DEFI pp.99–100).
- Flash-loan and flash-swap examples depend on atomic execution; their illustrated profits should not be treated as returns available from daily candles or as net of all execution costs (DEFI pp.101–102, 112–113).

## Verdict

None of the **NEW** ideas has both a compulsory-flow or redemption mechanism and a **measured** effect size in the book, so none meets the requested standard for a research card on this evidence alone. Collateral liquidation is the closest fit for a Binance price-response study, but needs independent event-level evidence of size and timing. The other candidates primarily require on-chain execution or stablecoin redemption infrastructure outside the listed venues; the book’s arbitrage profit is hypothetical (DEFI pp.71–72, 77, 101–102).

