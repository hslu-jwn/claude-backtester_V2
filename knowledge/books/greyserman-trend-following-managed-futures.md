# Alex Greyserman and Kathryn Kaminski, *Trend Following with Managed Futures: The Search for Crisis Alpha* (John Wiley & Sons, 2014)

Short: **TFMF**. Read 2026-11-18 by Codex.

The book studies systematic trend following in futures, from signal construction and position sizing to crisis behavior, portfolio diversification, capacity, and dynamic allocation. It combines a long historical reconstruction with simulations and managed-futures data. Its central subject is an already judged strategy family, though its treatment of portfolio construction and backtest limitations is useful.

**Citation limitation:** The supplied text has no discernible printed page numbers. Chapter references below identify the source passages; they are not substitutes for verified `TFMF p.N` citations. The PDF’s location in the library was not verified.

## Testable ideas

- **Diversified long/short trend following** (TFMF, ch. 1): The historical reconstruction uses monthly data, takes long and short positions across available equity, fixed-income, FX, and commodity markets, requires at least 12 months of history, and rebalances positions monthly to equal risk. The reviewed passage does not specify the exact signal and exit thresholds. The authors suggest hedger risk transfer and information dissemination among possible drivers, without identifying a compulsory counterparty flow for the measured return. They report **13 percent annual return and 11 percent annualized volatility** for the representative portfolio from the 1300s to 2013, using up to 84 markets as data became available. The authors caution that the historical data and assumptions are crude. Testing needs point-in-time market histories and executable costs; exchange futures are the closest project venue. **MAPS TO: diversified or single-symbol trend following at any speed.**

- **Allocate more to a trend strategy during its drawdown** (TFMF, ch. 17): Hold a fixed base allocation; use the remaining budget to increase exposure linearly as a negative trend signal in the strategy’s cumulative returns strengthens, reducing it as the signal weakens. The reviewed text does not provide a complete signal specification. The proposed mechanism is negative serial correlation in trend-strategy returns, not a counterparty required to trade. The book cites monthly manager-index evidence from 1993–2013 and warns of survivorship bias; **no realized size in bp per event or day is given**. Its allocation simulations exclude transaction and subscription/redemption costs. Testing would require point-in-time, net strategy return series and a fully specified allocation rule. This is a portfolio-management hypothesis rather than a new market-flow strategy. **MAPS TO: diversified or single-symbol trend following at any speed.**

## Method notes

- Construct historical universes from markets actually available at each date; the book explicitly questions historical data reliability and removes fixed-price gold during gold-standard periods (TFMF, ch. 1).
- Use total-return equity data when dividends matter. The authors contrast historical capital gains with dividend income to explain why price-only equity series can misrepresent returns (TFMF, ch. 1).
- Continuous futures series need roll-gap adjustments for signal calculation; actual trading still requires explicit handling of expiring contracts and execution (TFMF, ch. 3).
- Equal dollar risk allocation ignores cross-market correlations; equal risk contribution incorporates them. Capacity weighting favors larger, more liquid markets and can concentrate sector exposure (TFMF, ch. 3).
- Treat smaller-market diversification benefits alongside liquidity and market-impact limits. The book’s 2012 example reports low average agricultural-sector correlation, but this is a single-year snapshot (TFMF, ch. 15).
- Check whether a seemingly attractive allocation rule survives costs and whether its leverage is capped. Increasing exposure into a continuing drawdown can magnify losses (TFMF, ch. 17).
- Manager-track-record evidence of recovery after drawdowns can suffer survivorship bias: funds that fail to survive may disappear from the sample (TFMF, ch. 17).
- Separate collateral income from trading returns when comparing managed-futures performance; the book illustrates how cash yield can materially change reported Sharpe ratios (TFMF, ch. 6).

## Verdict

**No NEW idea qualifies for a research card** under the requested standard. The book’s main measured strategy maps to trend following; its drawdown-allocation discussion concerns timing an existing strategy and does not establish a compulsory counterparty flow or a realized bp-per-event effect. The missing printed page numbers also prevent the requested page-level citations from being completed from this text alone.

Read-only report: Reviewed the contents and selected trading, portfolio, and risk sections. **Files changed:** none. **Tests:** not run; no code was changed. **Open question:** printed page references require a paginated copy or another reliable page mapping.