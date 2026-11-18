# Antti Ilmanen, *Expected Returns: An Investor's Guide to Harvesting Market Rewards* (Wiley 2011)

Short: **ER**. Cite by chapter.section (`ER 13.3`); the extraction has no printed page numbers. Read 2026-11-18 by
5 Sonnet agents in parallel (Codex was at its limit; `knowledge/reading-brief.md`); PDF in the library folder Tier 1.
The map of return sources up to 2009: equity, bond, credit premia; value, carry, momentum, volatility selling;
growth, inflation, liquidity, tail factors; seasonals, cycles, survey and tactical forecasts. Most numbers are gross,
in-sample, 1960s-2009, and the author himself warns of data mining and decay.
Opus's reading against our ledger: (1) the forced-flow items are index changes (ER 5.2.6) and rating-threshold sellers
(fallen angels, ER 10.2): card I-122 (S&P 500 index changes, effect-size check first); (2) FX carry on FTMO pairs with
the real swap: card I-123, PARKED on power; (3) price-only cross-sections on US shares (MAX / lottery, betting against
beta, short-term reversal by VIX), curve-slope duration timing, correlation-spike market timing, Halloween: no card,
each fails M4 on our 2015+ share data or monthly-to-quarterly samples (halved Sharpe 0.3-0.4 -> expected t ~1);
(4) already spent: turn of month (H04 / H09 / I-67), FOMC drift (I-65), macro-release continuation (FB186), crypto
MAX (I-79), crypto BAB (FB013), commodity roll (I-115). Tooling notes worth keeping: strategy-level momentum
(own-sort autocorrelation +0.2, ER 20.2) and a crowding / de-leveraging risk filter for the long-short books.

# Part 1: Part I, ch.1-7: overview, historical returns, theory, behavioral finance, interpretations


Citation form: the extracted text has no printed page numbers, so references are ER chapter.section (e.g. ER 3.2).
Part I contains almost no trading rules. It is a framing and method section. Its value for us: (a) a catalogue of
return sources with sizes, (b) the "who pays and why" taxonomy, (c) honest-testing arguments, (d) a few flow and
segmentation mechanisms (index inclusion, rating-threshold forced selling, leveraged-arbitrage limits).

### Overview
- Ilmanen argues that expected returns must be judged from four inputs, not one: historical averages, theory,
  forward-looking indicators (yields, earnings yield, carry), and discretionary views (ER 1, the "elephant").
- Three lenses on return sources (the "cube"): asset classes (equity, duration, credit, alternatives), strategy styles
  (value, carry, momentum, volatility selling) and underlying risk factors (growth, inflation, illiquidity, tail risk).
- Core theory message: required return depends on WHEN an asset loses (covariance with "bad times"), not on stand-alone
  volatility. Strategies with steady small gains and rare big losses (carry, volatility selling, short-dated credit)
  earn a high premium and look better than they are until the tail event (2008 in his sample).
- Counter-message: the most volatile assets inside each asset class (high-vol stocks, 30y bonds, CCC bonds) had LOW
  long-run returns. Explanations: lottery preference and leverage constraints (ER 1.1, 6 note 6).
- Stance on testing: very humble. Any 20-year sample is one draw; realized return = expected return + windfall
  from repricing; paper (backtest) returns are overstated by overfitting, survivorship, ignored costs (ER 2, 4.6, 7.2).
- Behavioral vs rational: every anomaly has a rational (risk premium) and an irrational (mispricing) story and data
  rarely separate them; limits to arbitrage explain why mispricing persists (ER 5, 6, 7).
- No lookahead-sensitive rules are given; all the quantitative tables (Table 2.1, 3.1-3.7) are in images/tables not in
  the text, so exact numbers below are only those quoted in prose.

### Chapter notes

### Ch 1 - Introduction (ER 1.1-1.5)
- Historical averages mislead when (i) sample start/end sit at extreme valuations, (ii) expected returns vary over
  time (high realized return in a period often means LOW forward return, e.g. equities 2000), (iii) reported track
  records have survivorship / voluntary reporting bias, (iv) paper portfolios are overfitted and ignore costs.
- Headline long-run facts: global equities beat long government bonds by 3.7% and bills by 4.4% per year (real
  compound 5.4%, 1900-2009). Long bonds beat short bonds by only 0.5-1%; corporates beat governments by 0.3-1%
  (low end investment grade, high end high yield). Reward for rate risk and credit risk is most consistent at SHORT
  maturities and high ratings, not at the long/low-rated end.
- Value, carry, momentum "worked in many markets and added several percentage points a year"; the author concedes
  results are often overstated by overfitting but says prevalence makes it unlikely they never existed.
- Momentum horizon: continuation over multi-month horizons, mild reversal over multi-year horizons (ER 1.1).
- Volatility selling (writing equity index options) earned positive long-run returns, justified as selling
  catastrophe insurance.
- Bad-times timing: small caps had best long-run return and worst loss in the three worst years (1974, 1981, 2008);
  trend following was a surprisingly consistent safe haven in bad times (ER 1.2).
- Endogenous feedback: popularity of a winning strategy -> inflows -> overcrowding -> forced exits by leveraged
  traders; contributes to short-term momentum and long-term reversal (ER 1.3).
- Sharpe ratio is "investment language" for statistical significance; he rarely shows t-stats because time variation
  makes classical inference inappropriate (note 7).
- Credit spread leakage example: investment-grade index earned only about a quarter of the ~100bp average spread;
  the worst leak was index investors selling "fallen angels" (BB) that then performed well (ER 1.3, 3.2).

### Ch 2 - Historical averages and forward-looking returns (ER 2.1-2.3)
- Table 2.1 (1990-2009, not reproduced in text): duration risk rewarded (global government bonds SR about 0.8, best of
  traditional assets), equity and credit risk barely rewarded. Global equities lagged bonds, dragged by Japan (about -2%
  a year) while US/Europe made over 8%.
- Return vs volatility across asset classes was positive, Sharpe vs illiquidity also positive (less liquid assets
  have understated vol, hence inflated SR). Within an asset class the relation is not positive.
- Sample specificity: moving the end date from 2009 to 2008 to 2007 changed the equity-bond verdict. Long-run
  Sharpe ratios collapsed in 2008 for lottery-selling strategies: equity index volatility selling SR 1.3 -> 0.4;
  FX carry and short-dated credit carry (SR near 1) and convertible/fixed-income arbitrage hedge funds also dropped.
- Windfall (repricing) adjustment: US Treasuries 1990-2009 earned 6.8%; yield fell from about 8% to 3.5%, duration about
  5 -> roughly +1% a year of windfall. Without it: 5.8% and SR 0.32 instead of 0.53. Emerging-market debt spread fell
  10% -> 3% and got +2% to +5% a year windfall. S&P 500 P/E went about 15 -> 20 (ER 2.2).
- Box 2.1: 1982-2001 10y Treasury yield averaged 8.1% but realized 10.7% (yield fell 14.4% -> 5.1%); equity E/P fell
  12.4% -> 4.0%, about 6 of 15.5 percentage points of annual return was repricing.
- Note 3 (important for us): annual SR must exceed about 0.44 for significance with 20 years of data (critical value
  1.95, SR times sqrt(N)). A monthly predictive correlation of 0.10 (R2 1%) is "already a good basis for a profitable
  trading rule"; slow indicators with 0.55 long-horizon correlation are usually overfitted and give few independent bets
  (note 5). Predictive correlations are in-sample and overstate real value.
- Forward-looking value indicators (smoothed E/P, real yields) predict multi-year equity returns better than past
  returns; carry = return if market conditions are unchanged (yield, roll, payout).

### Ch 3 - The historical record in longer perspective (ER 3.1-3.6)
- Equities: Fama-French style results: small beats large, value beats growth in both 1990-2009 and 1926-2009; small
  growth ("lottery tickets") worst. Rolling 10-year windows: market premium negative 15% of the time, value negative 4%,
  momentum negative 10%, size negative 32% (20% if small-growth excluded).
- Short-term reversal and 12-month momentum have the highest GROSS paper returns, concentrated in small caps and
  high turnover; net of costs value and momentum earn about the same (Ghayur et al. 2010) and reversal gross double-digit
  returns would be negative after costs (ER 3.1). This is the cost wall in the author's own words.
- Bonds: duration reward rises steeply to 2-5y and flattens (hockey stick) over 1952-2009; the 1990-2009 monotonic
  rise is windfall. Credit: IG corporates +0.3% over Treasuries since 1926, junk +about 1% since 1953; BB (first
  below-IG) had the best long-run return; CCC poor. Fallen angels beat original-issue HY 9.6% vs 5.7% (1997-2009).
- Spread capture (ex post excess return / ex ante yield spread, 1990-2009): corporates only 21% (27bp of 129bp);
  1-3y corporates 64%, 1-10y 33%, long 15%; agencies above 100%; mortgages 40%. Duration-adjusted excess return of
  IG credit 0.2%, HY 1.7%.
- Active/other: commodity trend and equity value, FX carry had impressive baseline SRs but costs would reduce them;
  hedge funds had highest SR (biased and smoothed); VC 16% return but 39% a year in the 1990s and -3% in the 2000s.
- FX 1990-2009: high-yield currencies earned the highest average returns because carry was amplified by net
  appreciation (the opposite of uncovered interest parity). Cross-section of average returns vs average yield was
  near monotonic in G10 since 1990 but not in 1971-1989 static positions, though dynamic carry made money then too.
- TED spread (deposit minus bill) averaged about 70bp; only the Treasury can fund at the bill rate, so the premium
  for leaving bills cannot be arbitraged by leveraged players.
- Gold futures vs spot earned the same average because negative roll (contango) offset the T-bill collateral return;
  crude roll was mildly negative on average and positive until 2004 (ER 3 note 3).
- Real-return tables by decade: 1980s-90s best decades for most assets, 2000s among the worst.

### Ch 4 - Terminology (ER 4.1-4.6)
- Time-series predictability (one asset over time) vs cross-sectional (many assets at one time); cross-sectional
  trades are safer because directional risk can be hedged.
- Expected vs required vs hoped-for return: surveys of hoped-for returns are negatively related to feasible returns
  after rallies (Box 4.1).
- AM vs GM: GM is about AM minus half the variance (20% vol -> about 2 points).
- Currency: local excess return is approximately the currency-hedged return (covered interest parity); hedged return =
  home deposit rate + foreign excess return. Hedge only expected proceeds; shorter hedging horizon is more accurate.
- Sharpe ratio is scale invariant, ignores timing of losses and higher moments; information ratio is the relative
  analogue; "return divided by vol" without subtracting cash is wrong.
- Alpha shrinks as more factors are added to the model. Biased returns: published track records and backtests are
  upward biased (ER 4.6).

### Ch 5 - Rational theories (ER 5.1-5.3)
- CAPM old world: one factor, constant premia; empirical beta-return relation weak or negative in recent decades.
- New world: price = E[SDF times payoff]; premium of an asset = its covariance with "bad times" (high marginal utility).
  Safe havens (Treasuries since late 1990s) can have negative premia; but safe-haven correlation is unstable
  (bonds were no haven in the 1970s inflationary recessions; note 7).
- Strategies with best SR since the 1980s are the ones that lose in bad times (sell tail insurance); their high SR
  is largely compensation for that timing, not free money. Losses also coincide because of liquidity and positioning
  (1998, 2007, 2008), not only fundamentals.
- Multi-factor models; empirical factors (value, size, momentum, short and long-term reversal, volatility, liquidity,
  distress, accruals, asset growth, net issuance) are more prone to data mining unless an economic logic backs them.
- Time-varying premia: countercyclical expected returns (high near business-cycle troughs, Fama-French 1989);
  wealth-dependent risk aversion acts like portfolio insurance (sell when poorer) and amplifies booms and busts (ER
  5.2.3). Volatility and mean return link weak: high vol depresses current price but does not reliably predict higher
  near-term return.
- Skewness: co-skewness with the market is priced; investors overpay for lottery-like and downside-protection payoffs
  (ER 5.2.4).
- Supply and demand (ER 5.2.6): downward-sloping demand curves for stocks. S&P 500 inclusion causes a sudden,
  persistent price jump from index-fund buying; larger when the stock lacks close substitutes (Shleifer 1986,
  Wurgler-Zhuravskaya). Segmentation: many investors may hold only investment-grade bonds, so BB "orphans" are
  structurally cheap; new assets (TIPS 1997) cheap until they find a home; Treasury specialness in repo; Palm/3Com
  scarcity. Overcrowding only matters when levered traders hold concentrated positions.
- Disagreement plus short-sale constraints predict low returns for overvalued stocks. Delegated management creates
  momentum and reversal through flow chasing (Vayanos-Woolley).
- EMH: active management zero-sum before costs, negative after; Grossman-Stiglitz needs some inefficiency; Lo's
  adaptive markets; micro-efficient but macro-inefficient markets (relative pricing right, aggregate level wrong).

### Ch 6 - Behavioral finance (ER 6.1-6.4)
- Limits to arbitrage: fundamental risk, noise-trader risk, delegated capital (withdrawals when mispricing widens),
  leverage and margin, VaR-based risk control that forces deleveraging, crowding in smart trades (downside correlations
  higher than normal). Mispricings persist most where there is no close substitute, slow correction, or high model
  uncertainty.
- Biases: availability, representativeness (law of small numbers: gambler's fallacy when the process is known,
  extrapolation when unknown -> retail extrapolates, professionals expect reversal), conservatism (underreaction to
  statistically heavy but dull evidence), overconfidence, self-attribution, hindsight.
- Prospect theory: loss aversion (losses about 2-2.5 times gains), overweighting small probabilities (lotteries and
  insurance both demanded), narrow framing, disposition effect, house money effect, ambiguity aversion, regret.
- Mood/calendar claims: holiday effects, weather, lunar cycles are mentioned as likely data mining and too weak to
  survive costs (ER 6.2.2).
- Bubbles (Shiller four elements, Minsky stages, Soros reflexivity); equity premium puzzle pointer.
- Cross-section: value (LSV contrarian view vs FF risk view); DeBondt-Thaler reversal over 12-36 months; Jegadeesh-
  Titman momentum for up to 12 months; very-short-term (days to a month) reversal is explained mainly by bid-ask
  bounce and price concessions for large trades, not behavior (note 7). Four models explain momentum+reversal
  (DeLong positive feedback; Barberis-Shleifer-Vishny conservatism+representativeness; Daniel-Hirshleifer-
  Subrahmanyam overconfidence; Hong-Stein newswatchers and momentum traders). Post-earnings-announcement drift =
  underreaction.
- Disposition effect and momentum (ER 6.3.2): if most holders bought far above the current price, bad news travels
  slowly; if far below, good news travels slowly. Needs turnover/holder cost data to estimate the aggregate
  reference price.
- Memory effects: premia stay elevated for years after a salient shock (bond premium after 1969-82 inflation;
  post-1987 crash premium in index puts for 10-20 years; ex ante equity premium high 20 years after 1929).
- Conclusion: published regularities weaken or vanish after publication (data mining and learning); both rational
  and irrational forces matter; behavioral finance is used by the industry to justify active management although the
  limits-to-arbitrage message is that it is hard.

### Ch 7 - Alternative interpretations for predictability (ER 7.1-7.2)
- Three readings: time-varying risk premium, inefficiency, mirage. Inefficiencies should show a life cycle
  (decay once known), rational risk premia should not. Some alpha (value, FX carry) has morphed into beta.
- Mirage list: data mining (many choices, negative results unpublished, computing power), reporting bias (fund
  databases), peso problem (rare event not in sample -> selling insurance looks safe: no double-digit crash after 1987
  made put-selling look great for 20 years; Mexican peso 1955-76 carry), learning (bond market under- then
  over-predicted inflation), market frictions (paper profits largest in illiquid and high-turnover strategies; check
  costs and market impact), changing world (EMU, decimalization, Reg FD).
- Mitigations he lists: true out-of-sample, economic logic, cross-validation on another dataset, extensive robustness
  (subperiods), simple specification, conservative parameter estimates, no in-sample coefficients; the hindsight
  selection of indicator variables remains. Best fix is real out-of-sample time.
- Hard decision rule question: when a strategy underperforms, whether to cut or double down depends on whether the
  source is believed to be a sustainable risk premium or a mirage; data help little.

### Topic tags

- trend: Trend/momentum works multi-month (to 12 months), reverses over multi-year horizons; commodity trend was a
  high-SR style but costly (ER 3.3); trend following was a consistent bad-times safe haven (ER 1.2). Retail
  extrapolates when the process is ambiguous (Box 6.1).
- breakout: not covered.
- mean-reversion: very-short-term reversal (days to one month) is largest gross, mostly bid-ask bounce and price
  concessions, negative after costs (ER 3.1, 6 note 7); 12-36 month reversal and value are slow (ER 6.3.2). Mean
  reversion in valuation ratios drives time-varying expected returns.
- momentum/oscillators: momentum 3-12 months; behavioral models (underreaction then overreaction, disposition effect,
  delegated flow chasing); post-earnings drift. Momentum and value are negatively correlated, so the combination is
  smoother (ER 1.5).
- patterns: none; the book distrusts pattern-seeking (representativeness, seeing trends in random series).
- intraday/sessions: not covered.
- seasonality/time: holiday/weather/lunar effects dismissed as weak and cost-fragile (ER 6.2.2). Ch 25 (seasonals) is
  outside this range.
- volatility: all volatility is not equal; low-vol/high-vol puzzle (high-vol assets earn less); volatility clusters
  (GARCH); vol selling is a tail-risk premium with peso risk; vol-return link in time series is weak (ER 5.2.3).
- stops-and-exits: wealth-dependent risk aversion behaves like portfolio insurance; stop-loss and VaR rules can
  create vicious circles at market level (ER 5.2.3, 6.1, note 5.5 on the 1987 crash).
- position-sizing/risk: leverage constraints explain why safe assets are underpriced; leverage on low-vol assets
  boosted returns; Sharpe ignores timing of losses; correlations spike in crises (1998, 2007-08).
- testing-and-robustness/overfitting: see Ch 2.2, 2 note 3 and 5, Ch 7.2; windfall adjustment; SR significance bar;
  subperiod and different endpoint checks; published effects decay; simulated results overstate future.
- costs/execution: paper returns largest in illiquid/high-turnover strategies; costs eat reversal fully and
  momentum/value partly; market impact is usually understated (ER 3.1, 7.2).
- psychology/discipline: overconfidence, hindsight, disposition, loss aversion; the "cut or double down" dilemma;
  the author warns behavioral finance encourages overtrading.
- portfolio/diversification: negatively correlated return sources are valuable (value vs momentum); 60/40 risk is
  more than 90% equity; style and factor diversification beats asset-class diversification; diversification and
  rebalancing return is mentioned for Ch 28.

### Return sources with historical size (as quoted in prose of this part)
Everything gross of costs unless stated; period and size as given by the author.
- Equity over long bonds / bills, 1900-2009 global: +3.7% / +4.4% a year (real compound equity 5.4%). US 0.5-0.8 higher.
  In 1990-2009 equities did NOT beat bonds (global SR 0.18 vs bonds 0.79).
- Duration extension: 0.5-1% a year long-run (peaks at 2-5y maturity); in 1990-2009 much larger due to windfall
  (Treasuries +1% a year windfall; unhedged long bond SR since 1900 only 0.11-0.13). Payer: forced buyers (pension,
  index) vs the "term premium" for bearing inflation/rate risk.
- Credit: IG +0.3% (duration-adjusted 0.2% in 1990-2009), HY +1% long-run (1.7% duration-adjusted since 1989); spread
  capture 21% overall, 64% at 1-3y. Mechanism: forced selling at IG threshold (BB orphan/fallen angel), default losses
  small, index-rule selling leakage.
- Size / value / momentum premia: negative in 32% / 4% / 10% of rolling decades (long US history from 1926); value and
  momentum net of costs about equal; reversal gross double digit but negative net.
- FX carry: positive 1990-2009 with SR near 1 until 2008 then losses; carry strongest cross-country; yen the haven.
- Equity vol selling: SR 1.3 until mid-2008, 0.4 after; peso problem.
- Hedge funds: SR highest 1990-2009 but biased and smoothed; VC IRR 16% biased.
- Money-market: bills vs deposits (TED) 3.8% vs 4.5%, gap = credit and liquidity compensation that leveraged
  arbitrage cannot close because only the Treasury funds at the bill rate.
- Lottery avoidance: high-vol stocks, long Treasuries and CCC bonds lag within class; small growth worst of the FF 6.

### Testable ideas
Honest framing: Part I gives few precise rules; the items below are the ones that can be built on our data
(M1 CFDs, daily Alpaca US shares 2015+, Binance crypto perps with funding and taker flow, FRED yields, Cboe VIX futures,
EIA futures 1-4, Yahoo 10y futures, COT). None contain the author's own backtest numbers except where stated.

1. ★ **Lottery / high-volatility underperformance on US shares (low-vol minus high-vol, or MAX effect)** - Rule: each
   week rank liquid US shares by trailing 60-day daily return volatility (or maximum daily return of the past month);
   long lowest decile, short highest decile, dollar neutral (or beta neutral), hold one week, no leverage assumptions at
   first. Defaults to test: 60d vol window, 10 deciles, weekly rebalance; cost model for real shares, borrow fee on
   shorts. - Source: ER 1.1, 5.2.4, 6 note 6, Part II ch 19 (outside range). - Author claim: high-vol stocks, long
   Treasuries and CCC bonds all show low long-run returns; qualitative, no number here. - Fit: good for daily bars (we
   have 23,700 shares), cost-wall risk is lower than reversal because turnover is low; short side needs borrow cost and
   small-cap micro stocks must be excluded by a price/volume filter. - Different from failed families: cross-sectional
   share sort on a risk characteristic, not a price pattern; counterparty is leverage-constrained buyers of lottery
   payoffs (a structural demand, not a forced trade).
2. ★ **Index-inclusion price pressure (S&P 500 / index additions and deletions)** - Rule: for stocks announced for
   inclusion, long from the announcement close (or effective-date minus N days) to the day after effective date; for
   deletions short or avoid; test N in {1, 5}. Variants: stocks with few close substitutes (low correlation to existing
   members). Size per name small, portfolio of overlapping events. - Source: ER 5.2.6 (Shleifer 1986,
   Wurgler-Zhuravskaya). - Author claim: sudden and persistent price jump on inclusion. - Fit: good if we can build a
   list of constituent changes with announcement dates (external list needed, not in our data; Alpaca daily bars cover
   the price side). The edge has decayed in recent decades (author warns effects fade after publication), so power check
   first; sample of about 20-30 changes a year over 2015+. - Different: index-fund FORCED buyer, same family as our
   spent month-end index flow test but an event study on single names rather than a calendar rule.
3. ★ **Capital gains overhang (disposition effect proxy) on US shares** - Rule: for each stock compute a reference
   price = turnover-weighted average of past prices over the last 250 days (using daily volume as the weight). Overhang
   = (price - reference) / price. Sort monthly or weekly; long stocks with large unrealized gains held by holders (price
   well above reference), short large unrealized losses, or condition momentum on it. - Source: ER 6.3.2 (disposition
   effect, holder reference points). - Author claim: bad news travels slowly when holders sit on losses, good news slowly
   when they sit on gains; he gives no performance. - Fit: needs only daily price and volume (we have both); note it is
   a conditional momentum idea, so overlap with a generic momentum test, and the claim is mine to verify. Low turnover
   if monthly. - Different: holder-behavior state variable, not a price pattern or breakout.
4. ★ **Cross-sectional momentum and long-term reversal on crypto perps (weekly)** - Rule: each week rank perps by return
   over 4-13 weeks skipping the most recent week; long top, short bottom; also a 52-week reversal leg. Use funding
   as cost and taker-flow sorts as the existing Strategy 20 check. Defaults: formation 12 weeks, skip 1, hold 1-4 weeks.
   - Source: ER 1.1, 3.1, 6.3.2 (12-month momentum, 12-36 month reversal in equities, momentum in other assets).
   - Fit: good on daily/weekly crypto data we already hold; funding drag matters; the existing crypto taker-flow sort
   already passed so test incremental information (is momentum already inside it?). - Different: cross-sectional (not
   single-asset CFD trend), weekly horizon, and swap is replaced by funding.
5. ★ **Treasury duration extension decomposed (carry vs repricing) and yield-curve-slope timing** - Rule A: split the
   month-end duration extension result into carry (yield income) and capital change (duration times yield change); check
   the edge is not a sample windfall from falling yields (apply the Ch 2 windfall adjustment). Rule B: hold 10y
   futures in proportion to (curve slope minus slope implied by the short-rate level) or ex ante term premium proxy.
   Author warns raw slope is contaminated by rate-level mean-reversion expectations (1981 flat, 2010 steep).
   - Source: ER 2.2, 1.3, 3.2. - Fit: good, uses FRED and Yahoo 10y futures. - Different: macro bond premium, not
   a calendar flow; as a method check on an existing passed stream it is mostly a robustness step.
6. **Funding-rate carry across crypto perps (carry-capture ratio)** - Rule: long the lowest funding perps, short the
   highest (or delta-neutral cash-and-carry where possible); evaluate "carry capture" = realized excess return divided
   by average funding differential, the same ratio the author uses for credit (21% for corporates). - Source: ER 3.2
   (Table 3.3), 2.3 (carry definition), 3.4 (FX carry). - Author claim: yield seeking pays more across countries
   than within; carry has negative skew and lost heavily in 2008. - Fit: good (funding data in hand), tail risk in
   deleveraging episodes; likely to share a factor with Strategy 20. - Different from failed: carry is the counterparty
   paying a leverage premium; not previously tested in the list given.
7. **FX carry via CFD swap rates (dynamic long-short, G10)** - Rule: monthly rank pairs by broker swap (long-high,
   short-low), hold; vol-scale. - Source: ER 3.4 and Ch 13 (outside range). - Author claim: high-yield currencies
   earned highest returns 1990-2009, SR near 1 pre-2008, big losses in 2008. - Fit: poor-to-medium: FTMO swap includes
   a broker markup and the sign convention is asymmetric, so the "carry" is mostly taxed away; test with actual swap
   table before any signal work. - Different: cross-sectional, swap is the signal, but still costed through swap.
8. **Post-shock conditional long (equity index CFD / US shares) after drawdown or VIX spike** - Rule: go long an index
   after a drawdown of at least X% (X in {10, 15}) from a 252-day high or after VIX closes above its 90th percentile;
   exit when drawdown halves or VIX normalizes. - Source: ER 1.3, 5.2.3, 6.3.1 (countercyclical expected returns,
   memory effects). - Author claim: expected returns higher after adverse events, "especially in recessions", not
   a trading rule. - Fit: medium; few independent events, overlaps with VIX tests already spent; swap on long CFD. - Weak
   for t >= 3 given the small number of episodes.
9. **Spread/threshold forced selling (BB orphan / fallen angel) proxy via ETFs** - Rule: not testable with our data
   (no credit index data). Listed so that the mechanism is on file: restricted holders sell at the rating cutoff, price
   overshoots, later rebound. - Source: ER 3.2, 5.2.6. - Fit: poor now; needs rating-change event data.
10. **Method: replace the t >= 3 / power rule with the Sharpe-significance bar** - Annual SR must exceed 1.95/sqrt(years)
    for a 5% two-sided test (0.44 at 20 years, about 0.65 at 9 years); include the author's point that a monthly
    predictive correlation of 0.10 is enough for a profitable rule and that in-sample long-horizon correlations of
    0.5 are not. Use as an extra power-check line in the research gates. - Source: ER 2 note 3 and 5.
11. **Method: windfall / repricing adjustment for every trend-dependent test** - Report returns with the valuation-change
    component removed (yield change times duration for bonds; multiple change for equity) and report with different
    end dates (end-year minus 1, minus 2) so one endpoint cannot carry a result. - Source: ER 2.2, Box 2.1.
12. **Method: tail-aware reporting for strategies that sell insurance** - For carry, funding, short-vol and ETF-premium
    ideas, report the loss in the three worst months and the SR with the worst 1-2% of days removed/added; require a
    peso-problem note stating which rare event is not in our sample (e.g. no 2008-type event in Alpaca 2015+). - Source:
    ER 1.2, 2.2, 5.2.1, 7.2.

### Warnings / pitfalls
- A single 20-year sample is one draw; endpoints matter (2007/2008/2009 gave opposite equity-vs-bond verdicts). Use
  several endpoints and subperiods; cumulative-return plots on a log scale, not averages alone (ER 2.2).
- Realized return contains windfalls from repricing (yield falls, multiple expansion); strip them before treating
  history as forecast (ER 2.2). High realized return can signal low forward return.
- Paper profits are largest in illiquid and high-turnover strategies and cost estimates (incl. market impact) are
  usually too low; short-term reversal's double-digit gross profits turn negative net (ER 3.1, 7.2).
- Selling-tail-risk strategies (carry, vol selling, short-dated credit, convertible arbitrage) look like alpha until
  the tail event; their SR is partly a peso problem and partly a reward for losing in bad times (ER 2.2, 5.2.1, 7.2).
- Data mining: many small choices accumulate; negative results are unpublished; published regularities decay after
  publication (data mining plus arbitrage learning). Economic logic, out-of-sample time and cross-validation help but do
  not fully remove it (ER 7.2).
- Rational vs irrational explanations are rarely separable; decay patterns can tell them apart (inefficiencies decay,
  risk premia do not) (ER 7.1).
- Crowding and leveraged arbitrage: smart trades have higher downside correlations; VaR rules and margin calls make
  losses coincide; use stress correlations, not calm-period correlations (ER 6.1).
- Illiquid or smoothed series understate vol and correlation, inflating Sharpe ratios (ER 2.1, 1.2).
- Simple volatility is not the right measure of risk; timing of losses matters; do not assume SR is comparable across
  strategies with different skew (ER 4.5, 5.2.1).
- Behavioral stories are too easy; there is a story for every anomaly. Insist on a pre-registered mechanism (ER 6.4).
- Hindsight bias: past outcomes look predictable; keep decisions logged before looking at results (ER 1.5, 6.2.1).

# Part 2: ch.8-10: equity, bond and credit risk premia


Citation style: no printed page numbers in the text file, so cites are ER chapter.section (e.g. ER 9.2).

### Overview
- Covers the three big "market-beta" premia: equity risk premium (ch 8), bond/term premium (ch 9), credit premium (ch 10). Almost all evidence is annual/quarterly, long-horizon, US data 1900-2009 (bonds 1952-2009, credit 1973-2009). Very little is daily/weekly or tradable at our frequency.
- Stance: realized average return is a poor proxy for expected return. Valuation repricing (P/E expansion, falling yields, spread tightening) produces windfall gains that inflate the historical premium. Forward-looking carry/value measures are preferred, and survey data is used to separate rate expectations from risk premia.
- Equity: historical US premium is large but partly a 20th-century/survivor/repricing artefact; adjusted ex ante estimate about 4% over bonds. Market timing signals exist (valuation, sentiment, credit/leverage, seasonals) but out-of-sample performance is poor and the author is sceptical.
- Bonds: the term premium is time-varying but the yield curve is a noisy proxy; main long-run driver is a level-dependent inflation premium; the stock-bond correlation (safe-haven role) matters. Duration extension at the very front end (bills to 1-2y) had huge Sharpe ratios because of market segmentation.
- Credit: realized excess return over Treasuries is tiny (about 0.2-0.5% a year for IG), much smaller than the quoted spread (about 120 bp OAS). The gap is explained by downgrading bias, forced index selling (fallen angels, bonds rolling below 1y maturity), spread widening. Only short-dated top-rated credit and BB/fallen angels paid consistently.
- Overall relevance for us: mostly conceptual. Very few ideas are directly testable on our data; the best are index-membership forced-seller logic (fallen angel analogue), carry/valuation sign tests, and method warnings (in-sample correlation, mean shift hindsight, long-horizon overlap).

### Chapter notes

### Ch 8 - Equity risk premium (ER 8.1-8.7)
- Terms (8.1): ERPC = equity return over cash, ERPB = over long Treasuries; ex post (realized) vs ex ante (expected); arithmetic vs geometric. Cap-weighted indices preferred; equal-weight and fundamental/inverse-volatility weighting historically beat cap weight.
- Puzzle (8.2): consumption-based models imply premium well below 1% vs observed 4-8%. Explanations the author likes: rare disasters (peso problem), structural uncertainty (political risk), long-run risk, Depression legacy. Behavioral: myopic loss aversion (annual evaluation justifies about 6.5% premium) and house-money effect (risk aversion rises after losses).
- Historical premium (8.3): US real equity return about 6.3% a year over 200 years, very stable; 20-year real returns range 1% to 13%. Premium over bonds was about 0.5% in the 19th century, about 10x higher in the 20th. Since the Civil War US equities almost never lagged bonds over 20 years, but in 2009 they had lagged bonds over 20 years (and 40 years vs 20y Treasuries, 1968-2009). Global (19 countries, DMS 1900-2009) premium is 0.5-0.8% lower than US. Biases: survivorship, easy-data (start after crises), peso problem.
- Windfall adjustment (8.3): three studies (DMS 2002, Fama-French 2002, Ibbotson-Chen 2003) strip unexpected repricing and find an expected US equity-bond premium near 4%. 1900-2009 decomposition of the 9.6% nominal return: 3.0% inflation + 4.3% dividend yield + 1.3% real EPS growth + 0.5% repricing (P/E 12.5 to 21.9). Required return about 9.1% ex repricing. Forward-looking today: 2.3% inflation + 2.0% D/P + 1% real growth, plus 0.75% buybacks gives about 5.6-6.4% nominal. MSCI World 1975-2009: 11.1% = 4.2% inflation + 2.9% dividend + 2.1% book growth + 1.5% multiple expansion; 2000s: real growth 3.8% but multiple contraction -8.3%.
- Box 8.1: no positive beta premium across stocks (1962-2009): high-beta stocks did not beat low-beta stocks; low beta did as well or better. Lottery-ticket demand for volatile stocks is the explanation the author favors (see ER 19.5).
- Carry (8.4.1): D/P fell below 3% in 1993 and below 2% in 1997 and so failed as a timing signal in the 1990s because buybacks replaced dividends (SEC safe harbor 1982; buyback yield above 1% most years after 1985). Best carry measure: dividend + buyback - issuance ("net payout"): correlation 0.27 with next-quarter and 0.42 with next-year equity return (1985-2009), also least persistent. Adding M&A cash flows hurts predictive power.
- Value (8.4.2): E/P ranged 2-18%. Yield-ratio / "Fed Model" (bond yield over E/P) was neatly mean reverting for about 50 years and is a decent relative-value signal inside one regime but fails at regime change (inflation/vol regime, stock/bond volatility ratio shifts: stocks about 7x as volatile as bonds pre-1950, about equal by 1980s, bonds under half in the 2000s). Earnings yield tracks inflation (money illusion, accounting distortions, inflation uncertainty); valuation has a "sombrero" shape vs inflation: peak P/E10 when inflation is 1-4%, low in deflation and high inflation (Fig 8.10). |inflation - mean| correlates 0.69 with E/P. Demographics: share of prime-age savers peaked Japan late 1980s, US about 2000.
- DDM (8.4.3): ex ante ERPB = D/P + G - bond yield. Key debate is G. 1950-2009 real EPS and DPS growth about 1.9% (matched GDP per capita) but below real GDP growth 3.1%; 1900-2000 real dividend growth lagged GDP/capita in 15 of 16 countries (global about 0 real). Cause: dilution (about 2% a year, Cornell 2010) from new firms. Arithmetic nominal EPS growth about 7% vs geometric real only 1-2%. Ex ante ERPB from the author's model peaked in the 1970s, fell below 1% around the 2000 tech peak, above 4% in 2003 and higher in 2008.
- Surveys (8.5): retail forecasts are extrapolative (UBS/Gallup 12-month expectation correlates over 0.9 with trailing 12-month return; 10-year expectation about 14% in 1998-2002); CFO and fund-manager ERP estimates 2.4-4.7%, positively correlated with VIX (0.61). Academics' mean 30-year premium 7% (1997) to 5.5% (2001) to 6.0% (2009). Composite "irrational expectations" proxy (extrapolation + analyst growth + money illusion) troughed 1981, peaked 2000, correlation -0.9 with objective E/P: subjective and objective expected returns are inversely related. Relative retail vs institutional equity share is a contrarian signal (Edelen-Marcus-Tehranian 2010).
- Timing (8.6): premium over cash is large, so timing needs high skill to compensate for time in cash. Table 8.6 in-sample correlations 1962-2009 with next-quarter excess return: valuation ratios 0.10-0.20; net-buyback-adjusted D/P about 0.27; CAY 0.21 (but in-sample fitted); output gap -0.22 in-sample, -0.14 out of sample; unemployment +0.15; ISM -0.21; consumer confidence +0.14; GDP growth about -0.11 to -0.13; broker-dealer leverage growth -0.20 (-0.35 since mid-1980s); Baker-Wurgler sentiment -0.11; average pairwise stock correlation +0.20 (high correlation = crisis = high future market return); stock-level average variance mildly negative. Vol and returns: contemporaneous correlation strongly negative, predictive weak. Retail flows are the best contrarian indicator. Equity momentum is mild, but trend-following has had some success for market timing.
- Seasonals (8.6): January effect (esp. small caps), Halloween effect (Nov-Apr stronger than May-Oct), holidays, turn of month, scheduled macro announcement days all have higher average returns. Few are exploitable after turnover costs; data mining probably contributed. Return predictability is stronger in recessions.
- Notes: [3] relative weight US vs ex-US has -0.4 correlation with next-year relative return; yearly rebalancing to 50/50 would have helped. [5] warns that in-sample correlation of D/P is inflated by a mean shift the econometrician "knows".

### Ch 9 - Bond risk premium (ER 9.1-9.7)
- Definitions (9.1): BRP = expected excess return of long bond over rolling short bonds; yield = expected avg short rate + BRP; curve steepness = rate expectations + BRP. Pure expectations hypothesis (zero premium) vs random-walk view (steepness is all premium); 1980s regressions favored the latter: a steep curve predicts high excess bond returns, not rising yields. Author argues mean-reverting rate expectations matter more than consensus says.
- Historical (9.2): US Treasuries 1952-2009, return vs duration is a "hockey stick": steep up to 2 years, flat afterwards; Sharpe ratios above 1 at the very short end (vs 1-month bill) declining with maturity. Average yield curve 1961+: about 80 bp higher at 7y duration than 1y (6.7% vs 5.9%). Rolldown adds 30-50 bp at intermediate maturities. Bond results dominated by yield rise to 1981 and fall after; reward-risk relation was steeply upward in the second half but downward-sloping beyond short maturities in the first half.
- Box 9.2 front-end richness: short T-bills were rich because natural holders (central banks, liquidity-driven investors) did not maximize return; arbitrageurs could not short 1-month bills to buy 6-12 month bills because their financing rate was much higher than the bill rate (segmented market). Opportunity declined steadily from the mid-1980s.
- Ex ante measures (9.3): curve steepness, Cochrane-Piazzesi (regress excess returns on five forward rates; tent-shaped coefficients -2.1, +0.8, +3.0, +0.8, -2.1, i.e. curvature), Kim-Wright term-structure model with survey anchor, and survey-based BRP (10y yield minus consensus forecast of average future bill rate; March 2010 about 0).
- Predictive correlations (9.4, Table 9.2, 1962-2009): 10y-3m slope vs next-quarter 7-10y excess return +0.21 (yield curve predicts returns, not yield changes; weaker in recent years); ex ante real yield +0.28 (quarter) / +0.69 (5 years); C-P BRP +0.24 / +0.32; survey BRP +0.19 / +0.67; slope 5-year only +0.06. Slope is rangebound +-400 bp and correlation of slope with bill rate -0.53 (-0.79 vs detrended bill rate): mean-reverting short-rate expectations offset the inflation premium, so the curve misses secular BRP trends (inverted in 1980-81 when ex ante BRP was highest, followed by large 1980s bond returns).
- Drivers (9.5): (1) level-dependent inflation risk premium (3-4% of nominal yield at 1980 peak, near zero later; BRP moved about one-for-one with expected inflation since 1983; cross-country evidence); (2) covariance/safe haven: stock-bond correlation was positive 1965-1997, flipped negative around 1998 (large negative spikes in 1987, 1998, 2002, 2008); a rise in inflation would hurt bonds triple (expectations, premium, lost hedge); (3) supply-demand: fiscal supply (share of >10y bonds in government debt predicts next-year excess return; 1% debt/GDP raises yields 2-6 bp), pension/regulatory demand, foreign flows (30-50 bp consensus, estimates up to 100 bp), Fed QE 2009 lowered 10y yield 40-80 bp (Gagnon et al. 2010), the announcement of discontinuing 30y issuance in Oct 2001 repriced within minutes; (4) cyclical: curve is countercyclical, inversion predicts recessions, steep curves at troughs. "Follow the Fed" rules have not worked since 1994. Box 9.3: much of the yield-curve return predictability reflects forecast errors (investors overestimate yield rises at cyclical troughs), not rational premia.
- Duration timing (9.6, Table 9.3, 7-10y Treasury excess return correlations): ex ante real yield 0.31 quarterly; quintile with highest real yield followed by +2.0% a quarter excess return, lowest quintile -0.7%. Safe-haven: prior equity return -0.15, equity vol +0.11 (one quarter). Long-horizon (5y) predictors: expected inflation 0.31, bond vol 0.64, debt maturity share 0.66, profit/GDP -0.52 (mostly one observation, the 1970s trough). Next-month best predictors (double-digit correlation): generic BRP proxies, carry/value measures, past-month equity return and past-month bond return; bond momentum works at very short horizons, not multi-month. Concave curve means duration-neutral steepeners earn a positive premium.

### Ch 10 - Credit risk premium (ER 10.1-10.8)
- Spread decomposition (10.1): raw spread = expected default/downgrade loss cushion + embedded option value + liquidity + true credit risk premium. Expected loss = default probability x (1 - recovery), recovery about 40% senior. IG break-even spreads (Elton et al.): 14 bp (A) and 40 bp (BBB) at 10y. Merton view: bondholder is short a put on firm assets, hurt by volatility; structural models predict spreads much below observed. Reduced-form models fit better but overfit.
- Historical excess return (10.2): long US corporates beat long Treasuries by only about 50 bp (DMS 1900-2000) or about 24 bp geometric (1926-2009; 41 bp if compounded differently); all of it came in the first 42 years. Barcap IG 1973-2009 average ex post excess return about 30 bp vs 120 bp average OAS. Information ratio at best 0.16 across IG rating classes. BB (just below IG) best category; fallen angels beat original-issue HY; CCC clearly worse than Treasuries since 1985 (lottery-seeking, reach-for-yield).
- Why so low (10.2, Table 10.2): realized excess 30-40 bp + spread widening losses 0-20 bp + index investors' forced selling 30-40 bp + default/downgrade losses 20-40 bp account for the 120 bp. Downgrade bias: A-rated bond twice as likely to be downgraded to Baa as upgraded to Aa; upgrade narrows spread 36 bp, downgrade widens 56 bp (spread roughly doubles per notch). Index rules force selling bonds that fall below IG or under 1y maturity or become too small; Ng-Phelps (2010) show IG index investors would have gained 38 bp a year (1990-2009), 32 bp from keeping fallen angels. Some mandates force this selling regardless.
- Front-end carry (10.3): overweighting AAA/AA 1-3 year credits (or swaps/agencies) vs Treasuries gave information ratio above 0.5 (above 1.0 before 2008) over 1988-2009 and rolling 2-year outperformance always positive from the late 1980s until late 2007. Mechanism: positive spread intercept at zero maturity + flat spread curve = large break-even cushion (spread/duration) and low spread volatility. Not arbitraged away because levered traders fund corporates near LIBOR but borrow Treasuries at repo near bill rate: after funding costs the Sharpe falls from 0.7 to 0.4 and return advantage to about 40 bp. Payoff resembles selling put options on systemic catastrophe (losses in 1998, 2007-08).
- Spread drivers (10.4): wide spreads predict higher excess returns (correlation 0.12 next month, 0.48 next year, 1973-2009). Aaa-Treasury spread inversely related to debt/GDP since the 1920s (Treasury scarcity). IG/BBB: cyclical (Baa-Aaa vs CFNAI), equity volatility and credit spreads move together. HY: driven by default rates; Moody's average annual default rate 1920-2009: IG 0.15%, spec grade 2.8% (since 1970: 0.08% and 3.9%); HY spread averaged 5.3% since 1978 vs 4.3% default rate and 2.6% net loss; cumulative 30-year excess return vanished in 2008. Giesecke et al. 1866-2008: avg default 1.5% of issues, spread 1.5%, 50% recovery implies 0.8% a year excess return.
- Tactical (10.5, Table 10.4, 1990-2009, IG excess return): corporate OAS +0.25 (quarter) / +0.46 (year); MOVE +0.19/+0.40; VIX +0.28/+0.39; 10y-2y slope -0.07/-0.37 per the table layout; 6-month equity momentum +0.15 / -0.32; credit excess-return momentum -0.10/-0.11; CFNAI -0.34/-0.31; profit/GDP and fiscal deficit also relevant. Credit shows short-term momentum and longer-term reversal.
- Other debt (10.6): swap-Treasury spread has negligible credit risk, driven by LIBOR-repo spread (15-30 bp normal), Treasury scarcity (30y swap spread hit 150 bp in 2000), and public finances; unstable determinants. CDS-cash basis blew out to several hundred bp in 2008. MBS: realized excess 28 bp vs 77 bp OAS (1989-99) and 28 vs 69 bp (1990-2009): prepayment efficiency improved, model OAS overstated. EM hard-currency debt: spread fell from 1000 bp (2001) to under 200 bp (2006); one of the best Sharpe ratios of the 1990s-2000s, but mostly one-off repricing.
- Conclusion (10.7): IG corporate advantage about 30 bp; only fallen angels and short top-rated credit paid consistently; Swensen argues for no strategic allocation to non-government debt.

### Topic tags
- trend: equity momentum mild but trend-following market-timing has had some success (8.6); bond market momentum works at 1-month horizon, not multi-month (9.6); credit has short-term momentum and long-term reversal (10.5).
- breakout: not covered.
- mean-reversion: yield ratio (bond yield / E/P) mean reverting about 50 years, fails at regime shifts (8.4.2); contrarian valuation timing (Fig 8.16, hindsight-inflated); long-horizon return reversal; retail-flow contrarian signal; rebalancing to constant weights has a mild contrarian bias.
- momentum/oscillators: past-month equity and bond returns predict next-month bond excess return (double-digit correlations, 9.6); 6-month equity momentum predicts next-year credit return negatively (10.5).
- patterns: none.
- intraday/sessions: none. Closest are scheduled-announcement days and turn-of-month with higher average equity returns (8.6, no numbers).
- seasonality/time: January effect (small caps), Halloween (Nov-Apr), holidays, turn of month, announcement days all higher average equity returns; "few can be exploited after turnover costs", data mining suspected (8.6). End of month rolling out of index (maturity under 1y) forced selling in credit (10.2).
- volatility: equity-vol vs future market return weak; high pairwise correlation (crisis) predicts high future returns (+0.20); VIX positively correlated with survey ERP (0.61); VIX and MOVE both predict credit excess return +0.2 to +0.4; credit/Merton: equity holders long vol, bondholders short vol; implied minus realized vol gap has some timing ability.
- stops-and-exits: none.
- position-sizing/risk: sizing front-end credit by ex ante opportunity helps long run but failed in 2008; short-dated credit is a put-writing payoff (rare, crisis-timed losses); lottery-preference explains poor CCC and high-beta stock returns.
- testing-and-robustness/overfitting: realized average != expected return (windfall repricing); in-sample correlations flattered by mean shifts known in hindsight (note 8.5); CAY is in-sample fitted; long-horizon predictability has overlapping data and small effective sample; profit/GDP -0.52 driven by a single observation (1970s trough); survivorship / easy data / peso problem; Welch-Goyal critique of equity predictability; many timing indicators fail out of sample (D/P in 1990s); seasonals partly data mined.
- costs/execution: seasonal equity effects not exploitable after turnover costs; funding-rate asymmetry (corporate funded at LIBOR, Treasury borrowed at repo) kills the front-end credit arb for levered players (Sharpe 0.7 to 0.4); index investors lose 30-40 bp from forced selling at month-end bid; corporate bond index volatility understated by stale pricing; trading cost of Treasuries lower.
- psychology/discipline: loss aversion/myopia explain equity premium; retail expectations extrapolative; timing needs tolerance for being "wrong and alone"; lottery preference.
- portfolio/diversification: stock-bond correlation sign flips (positive 1965-97, negative since 1998; spikes negative in 1987/1998/2002/2008 crises); Treasuries are a safe haven only in low-inflation regimes; annual rebalancing US vs ex-US to 50/50 would have helped (-0.4 correlation of relative weight with next-year relative return); beta is not rewarded across stocks.

### Testable ideas
(Most chapter content is low-frequency macro/valuation; these are the items that map onto our data. None is validated by the author at our horizon.)

1. **Fallen-angel / index-deletion forced seller (US shares analogue)** - ★ Rule: when a stock is dropped from an index or loses an eligibility criterion that forces holders to sell, trade the opposite side after the forced-selling window. On our data: stocks leaving S&P 500 / large-cap eligibility, or falling below a market-cap/price threshold, measured at daily bars (Alpaca daily). Buy at close after the effective-date selling pressure, hold N=20-60 days vs equal-weighted sector or market, rank by size of forced selling. Source: ER 10.2 (BB rated fallen angels beat original-issue HY; Ng-Phelps: 32 bp a year from keeping fallen angels; index selling at bid at month-end). Author evidence: bonds only, 1990-2009, roughly +0.3-0.4% a year at index level (not a stock result). Fit for our data: medium; needs index membership dates (we have only prices for about 23,700 shares, so we would have to proxy deletions by market cap rank or by a rule like drop out of top-N dollar-volume universe). Differs from failed families: counterparty must trade (mandate-forced), not a price pattern. Caveat: stock evidence is documented elsewhere and may be arbitraged; bond-specific mechanism does not transfer one-to-one.

2. **Month-end maturity/duration roll-down seller (extension of month-end flow)** - Rule: bonds (or bond futures / Treasury yield proxies) at the point when index rules force sales (remaining maturity under 1y, or 1y roll-down from 10y to shorter bucket), trade the 10-year continuous Treasury futures around the monthly index rebalance days. Source: ER 10.2 (index investors sell bonds under one-year maturity and fallen angels at month-end). Evidence: author gives only the average cost (30-40 bp a year). Fit: poor to medium (we have only Yahoo continuous 10y futures and FRED yields; no bond-level index data). Differs from the spent month-end duration extension test only by being per-bucket, so probably redundant. Mark low priority.

3. **Yield-curve-slope / real-yield duration timing on Treasury futures** - ★ Rule: monthly, go long 10y Treasury futures (Yahoo continuous) when 10y-3m slope (FRED) is in the top quintile of its trailing 10-year history or when ex ante real yield (10y yield minus a trailing 12-month CPI or a survey proxy) is in the top quintile; flat or short otherwise; hold one month. Add an optional filter: past-month 10y futures return positive (1-month momentum, ER 9.6). Source: ER 9.4, 9.6, Tables 9.2-9.3. Author evidence: slope correlation +0.21 with next-quarter 7-10y excess return (1962-2009, in sample, weaker recently); real yield +0.28 (quarter); top real-yield quintile quarterly excess return +2.0% vs -0.7% bottom; past-month bond return and equity return also have double-digit correlation with next-month bond excess return. Fit: good for data (FRED yields exist; futures are cheap in cost terms, no swap). Differs: macro/regime signal, not price pattern; but it is long-horizon, so power is the issue: only about 25 non-overlapping years of monthly data in our window, so a power check is mandatory. Caveat: author states the slope effect is partly forecast error and weakened over time; real yield needs inflation expectations (we have no survey; use trailing CPI from FRED).

4. **Safe-haven flip: long Treasury futures after equity drawdown / vol spike** - Rule: if the prior-month S&P/US500 return is below -5% or VIX is in the top quintile, go long 10y futures for the next month (author sees bonds rise after negative equity returns, and high equity vol is bullish for bonds). Source: ER 9.6 (correlations -0.15 and +0.11, next quarter) and stock-bond correlation negative since 1998 (9.5, Fig 9.10). Author evidence: weak (absolute correlations low, he says the evidence is weak). Fit: good (VIX futures and US500 CFD/FTMO daily plus Treasury futures available). Differs from failed families: cross-asset flight-to-quality flow, not a price pattern. Regime dependence: needs the stock-bond correlation to be negative; condition on a rolling 26-week stock-bond correlation below zero (ER 9.5).

5. **Stock-bond correlation regime filter for a bond long** - Rule: use the 26-week rolling stock-bond return correlation as a regime switch; go long 10y futures only when correlation is negative (low-inflation, safe-haven regime), flat when positive. Source: ER 9.5, Fig 9.10 (positive 1965-97, negative since 1998). Author evidence: descriptive only. Fit: good, low cost. Differs: regime filter rather than entry signal. Low-medium priority; best as an overlay on idea 3 or 4.

6. **Crypto funding / taker flow as "level-dependent premium" analogue** - Observation only: the author's repeated message that premia are time-varying and that the best signals are generic carry/value proxies (ex ante real yield, valuation) suggests testing for our crypto perps whether basis/funding level (carry) predicts next-week return of the perp as a whole, with high carry bullish for the carry-receiving side after costs. Source: ER 8.4.1, 9.6 (carry/value measures are best next-month predictors with double-digit correlations). No author evidence on crypto. Fit: good (funding data exist). Differs: carry-as-forecast rather than flow sort; may overlap with Strategy 20. Medium-low.

7. **Equity net-payout / buyback-carry cross-section on US shares** - Rule: monthly long-short on US shares sorted by net payout yield (dividends + buybacks - issuance); long high-payout, short high-issuance. Source: ER 8.4.1 (aggregate version has 0.42 correlation with next-year market return; cross-section evidence in other chapters of the book, not here). Fit: poor with only price data (we have no fundamentals; would need share counts, so issuance proxy via market-cap change minus return could be derived from Alpaca if shares outstanding are available). Mention only so we know the data gap. Low priority.

8. **Market-correlation spike as a contrarian long signal** - ★ Rule: compute the average pairwise correlation (or first principal component share) of daily returns across a liquid basket (our 34 CFDs, or US shares top 500); when it is in the top decile of its own trailing 3-year history, go long the broad index (US500/NAS100 CFD or a US index ETF in the shares data) for 1-3 months. Source: ER 8.6 (Pollet-Wilson: high intra-market correlation predicts high future market return, correlation +0.20 with next-quarter return; high average variance mildly negative). Author evidence: in-sample correlation about 0.20 (quarterly). Fit: good for index CFDs (long only, swap cost moderate but cost wall risk because hold time is weeks); better on futures-like venue. Differs: uses market breadth/dispersion state, not price level patterns. Needs a power check since the number of crisis episodes is tiny (2015-2025: about 6-8 spikes).

9. **Broker-dealer leverage proxy** - Rule: not testable directly (needs Fed flow of funds); but proxy: quarterly growth in leverage predicts next-quarter market return with correlation -0.35 since mid-1980s (ER 8.6). Fit: poor (data not in our list). Skip.

10. **Equity seasonality overlays (Halloween, turn of month, announcement days)** - Rule: hold the index only Nov-Apr (Halloween), or only around the turn of month, or only on scheduled macro days (CPI/NFP/FOMC). Source: ER 8.6. Author evidence: qualitative only, "few exploitable after turnover costs". Fit: poor to medium: month-end index flow is already spent; turn of month on index CFDs has swap cost; Halloween effect has few trades (2 a year) so no cost problem but extremely low power in a 10-year sample. Can be tested as a single pre-registered Halloween test on US shares/indices if power check says it can reach t >= 3 (it will not). Differs: calendar rule. Probably a fail on power, not a test candidate; included for completeness.

11. **Spread-widening buy for credit ETFs / HY proxy (US shares: HYG, LQD)** - Rule: when a credit-spread proxy (HYG vs IEF ratio, or HYG drawdown from a 52-week high) exceeds a threshold, buy HYG/LQD for 3-12 months; flat otherwise. Source: ER 10.4-10.5 (wide spread predicts excess return: correlation 0.48 next year; VIX and MOVE also bullish for credit). Author evidence: 1990-2009 in-sample, with risk of 2008 stumbles. Fit: medium: ETFs are in Alpaca daily data presumably; HYG begins 2007. Differs from failed families: credit factor, not price pattern. Long horizon again means power problem and very few independent episodes (2015-16, 2018, 2020, 2022).

12. **Front-end credit carry (short-dated top-rated vs Treasury)** - Not testable: needs bond indices or credit ETFs with matching durations (e.g. SHY vs VCSH / SPSB). A rough test is SPSB or VCSH vs SHY in Alpaca daily data. Author evidence: IR 0.5-1.0 over 1988-2009 unlevered; funding cost destroys levered version (IR 0.7 to 0.4). Fit: poor to medium; the edge is small (about 40 bp net) vs ETF spread costs; unlevered only. Low priority.

13. **Net-asset-weighted equity timing with the yield ratio** - Rule: long US index when 10y yield / E/P ratio is below its 10-year median, flat otherwise. Source: ER 8.4.2 (works inside one regime). Fit: poor (no earnings data; Shiller-type series not in our data; would need approximations). Skip.

Top 5 flagged: 1 (fallen-angel / index deletion forced sellers), 3 (curve/real-yield duration timing on 10y futures), 8 (correlation spike contrarian long), 4 (safe-haven flip), plus 5 as overlay (note: the four star ideas together are all low-frequency and will need strict power checks; idea 1 is the only real forced-counterparty idea).

### Warnings / pitfalls
- Realized average returns mislead when valuation changes occur (P/E expansion, falling yields, spread tightening, repricing of EM debt): the author repeatedly stresses that a long sample can still be dominated by one-off windfalls. Our short sample (10 years) has the same issue for any asset that re-rated.
- In-sample predictive correlations are overstated: hindsight about mean shifts (note 8.5), fitted factors (CAY), and single observations (profit/GDP vs bonds). Out-of-sample or quasi-out-of-sample selection needed.
- Long-horizon predictability has overlapping data, persistent regressors, tiny effective sample (author's own caveat, 9.6). For a 10-year dataset, any annual-horizon signal has about 10 independent observations.
- Timing indicators often fail precisely when needed (D/P below 3% in 1990s; yield curve inverted in 1980-81 before the best bond decade; yield ratio fails at regime shifts). Regime filters (inflation level, stock-bond correlation) should be explicit.
- Predictability may be forecast error, not a rational premium (Box 9.3); such effects can vanish when expectations adjust (the Fed-following rule broke after 1994; front-end Treasury richness shrank after the mid-1980s as arbitrage and investor learning rose).
- Strategies that look like free carry often have put-selling payoffs (front-end credit, HY): small steady gains and rare crisis losses. Compare on tail-aware metrics, not Sharpe only; stale-priced indices understate volatility and correlation.
- Funding asymmetries and short-sale/borrow constraints determine which "arbitrage" survives (levered vs unlevered): an edge visible in index data may not be capturable at our costs. Index returns ignore the trading costs of constituents (forced selling at bid, month-end rebalancing).
- Seasonals and calendar effects exist in averages but rarely survive costs and data mining; the author does not give numbers.
- Equity cross-section: no beta premium (Box 8.1): sorting stocks by beta gives nothing or the opposite; lottery-seeking explains why high-volatility assets (high beta, CCC bonds) underperform.
- Ex ante yield or spread overstates expected return (expected default loss, downgrade bias, embedded options, illiquidity); equally, quoted carry on futures or perps overstates it if roll/funding losses are ignored.

# Part 3: ch.11-15: alternatives, value, currency carry, commodity momentum and trend, volatility selling


Citation form: no printed page numbers in the text file, so cites are ER chapter.section (e.g. ER 13.3).

### Overview
- Covers ch. 11 (alternatives: real estate, commodities, hedge funds, private equity), ch. 12 (equity value), ch. 13 (currency carry), ch. 14 (commodity momentum and trend following, plus momentum in other assets), ch. 15 (selling index volatility).
- Stance: a mostly historical, premium-harvesting view. Each return source is explained as either a risk premium (losses in bad times, "selling catastrophe insurance") or a behavioral error (extrapolation, underreaction), and Ilmanen leans behavioral for value and momentum, risk-premium for carry and vol selling.
- Recurring warnings: long-run Sharpe ratios are inflated by benign samples (peso problem), reporting biases, no costs, and crowding; "alpha morphs into beta" as strategies become popular; style timing is mildly helpful at best and prone to overfitting.
- The ch. 11 material (real estate, art, private equity, hedge fund fees and biases) is mostly irrelevant to us, except the roll-return and commodity sections (11.3) and the hedge-fund bias taxonomy (a checklist for honest testing).
- Useful for us: cleanly stated mechanisms and historical sizes for carry, value, trend, vol premium, seasonal regularities (January, December), and the method lessons about biases, costs and crowding.
- No order book, flow or micro-level data in this part; flows only appear as index-roll pressure, return-chasing, year-end window dressing.

### Chapter notes

### Ch 11 - Alternatives (11.1-11.5)
- 11.1: Alternatives (real estate, commodities, hedge funds, PE) boomed 2002-07 and were crushed in 2008; they are procyclical, so their diversification fails when needed. Short-term momentum and long-term reversal appear in them too; money-flow (overcrowding) signals may be contrarian indicators.
- 11.2 Real estate: appraisal-based indices (NCREIF) are smoothed and stale, so volatility is understated and Sharpe overstated; "de-smoothing" can double volatility. Use positive return autocorrelation as a symptom of stale prices. Long-run numbers (1978-2008, nominal): commercial RE 10.0%, equity REITs 11.9%, residential 5.7%, large-cap stocks 10.8%; real house prices rose only about 0.3% a year over 120 years (Shiller).
- 11.2: valuation yardstick = rental yield or cap rate; changes in real house prices correlate -0.88 with changes in rental yield, so valuation change drives short-term price moves. Momentum is stronger than reversal in real estate but partly smoothing artifact.
- 11.3 Commodity futures return = spot change + collateral (T-bill) return + roll return. Roll return is positive in backwardation (downward-sloping curve), negative in contango.
- 11.3 Theories of the term structure: (a) hedging pressure (Keynes): producers sell futures and pay speculators a premium; (b) theory of storage: spot minus futures = convenience yield minus storage minus financing cost; backwardation when inventories are low, steepest before harvest in agriculture; spikes mean-revert.
- 11.3 History: S&P GSCI about 10% a year total return over 40 years, more than half of it T-bill collateral income; excess return from spot plus roll. Roll return was positive on average, but 2005-2009 annual roll losses ranged from -8% to -25% (oil moved to contango); the cumulative roll gain since 1970 was erased by 2009. Index investors rolling in sync at the same predictable time added pressure ("temporary price distortions that other traders can exploit or avoid") - this is the GSCI-roll idea, already spent for us.
- 11.3 Hong-Yogo (1965-2008): equal-weighted commodity futures portfolio, 7.08% a year excess, Sharpe 0.50, about half from spot, half from roll. Long-run average returns across commodities line up with average roll returns (oil, nickel, sugar backwardated and positive; natgas, aluminium, corn contango and negative). Crude roll return went from +6% (1992-2000) to -3% (2001-2009).
- 11.3: roll return has been weak for short-term market timing (extreme backwardation can coincide with spot spikes that then fade), but a cross-sectional rule "overweight backwardated, underweight contangoed" added value; aggregate backwardation predicts higher near-term returns; low short rates and inverted yield curve predict high commodity returns (Hong-Yogo). Momentum has been the best predictor of near-term commodity returns. Second-generation indices (trend tilt, roll tilt, deferred contracts) raise Sharpe but cost more.
- 11.3: diversification return: index geometric mean can be several points above the constituents' average (GSCI arithmetic 12% vs geometric 10%, vol 20%). Footnote 5: use proper excess-return series including roll; generic nearby price (CL1) is not a strategy return (oil flat near $71 mid-2007 to mid-2009, but excess return -36% from negative roll).
- 11.4 Hedge funds: bias taxonomy (survivorship 2-3%, backfill 2-4%, selection, liquidation, lookback, lookahead biases). Ibbotson-Chen-Zhu: equal-weighted TASS 1995-2009 return 14.3% live-only, 11.1% with dead funds, 7.6% after backfill adjustment (total bias 6.6%). Net-of-bias gross return 11.4% = 3.8% fees + 4.6% beta + 3.0% alpha.
- 11.4: HF index returns are market-directional, with hidden short-volatility and tail risk; half of the worst 12 months of HFR were in 2008; diversifying across funds raises negative skew and fat tails. Investors' own (dollar-weighted) returns trail buy-and-hold by 3-7% a year via return chasing (Dichev-Yu). December is clearly the best month for hedge funds as a group (year-end marking of illiquid assets).
- 11.4 CTAs (Box 11.4): reported CTA return 1994-2007 falls from 12.6% to 4.9% after survivorship and backfill adjustment (3-year filter: 7.7%); gross return 5.4% over T-bills but only 0.9% net of fees; CTA gross returns lag simple trend rules.
- 11.4 Alpha vs beta: alpha is "return not explained by common factors of a given model"; as factors are discovered, alpha is reclassified as alternative beta (value, carry, momentum, vol selling). Alpha pool net of costs is negative-sum among active investors; any edge needs a counterparty who tolerates losses.
- 11.5 Private equity: reported IRR numbers are not comparable to returns; after fees PE roughly matches or lags the S&P 500 (Kaplan-Schoar; Phalippou: -3% a year, risk-adjusted -6%). Skip.

### Ch 12 - Value-oriented equity selection (12.1-12.7)
- 12.1: dynamic strategies have more degrees of freedom, hence more overfitting; the basic findings (value, carry, trend, vol selling) are supported out of sample, while "refinements" may be overfit. Crowding or learning can still weaken them.
- 12.2: Fama-French VMG (high minus low book/price, small and large legs, cheapest 30% long, richest 30% short): US 1926-2009 value premium 4.1% a year compounded (Sharpe 0.39, same as the equity premium 5.7%); non-US composite 1975-2009 Sharpe 0.78; global composite Sharpe 0.68. Value premium has about the same size before and after 1963 (the Compustat era). VMG ignores trading and short-financing costs and uses deliberately long publication lags.
- 12.2: VMG market beta was +0.35 (1926-63) and -0.28 (1963-2004); four drawdowns beyond 30%, three in the 1930s and one in 1999-2000. Source of value return: mostly convergence of valuation ratios (profitability mean reversion), dividends about half of large-cap value premium but almost nothing for small caps.
- 12.2 Design choices: valuation ratio (E/P, B/P, CF/P, sales/P, enterprise-value variants), publication lag, rebalance frequency, sector neutrality (sector-neutral improves risk-adjusted return, e.g. Sharpe 0.68 vs 0.37 in one UBS sample, one third less volatility), large vs small caps (premium larger in small, low-institutional-ownership stocks, which are about three quarters of names but under a tenth of cap).
- 12.2 Fundamental index (Arnott et al.): weighting by sales, cash flow, book, dividends beat cap weighting by about 2% a year over 40 years; Ilmanen calls it a value tilt, and part of the edge may be avoiding index-inclusion/exclusion flows ("buying new index constituents and selling excluded stocks with the index-tracking crowd"). Any price-indifferent weighting (equal weight, inverse vol, min variance) beats cap weight via implicit rebalancing/contrarian bias.
- 12.3 Style timing: weak and overfit-prone. Mildly useful: (a) value-return momentum over one month; (b) value spread (valuation gap between value and growth quartiles; correlation with next-year outperformance 0.48 raw, 0.43 sector-neutral; next-month 0.29/0.20; spread was narrow in 1998 and 2007 before sharp underperformance); (c) seasonal: VMG January average 2.2% vs 0.24% in other months (1926-2008, US; also Japan and continental Europe, reversed in UK); no Halloween effect for value; (d) macro and liquidity: weak links.
- 12.4 Why: behavioral (extrapolating past earnings growth; glamour stocks have negative returns on earnings announcement days, value positive; growth expectations overpriced by about a factor of 2) vs rational (distress, bad cash-flow beta, investment factor). Distress-risk filters help: junk-rated and distressed names earn poor returns and drag value; filter by quality, profitability, momentum. Anomalies concentrate in high-credit-risk stocks (under 10% of cap) around downgrades (Avramov et al.).
- 12.5: value works across assets (AMP 2009): stock selection in 4 regions, country equity, currencies, bonds, commodities; naive indicators: P/B for stocks, price 5 years ago (commodities), 5-year past return (currencies), real yield (bonds). All Sharpe ratios positive (0.1 to 0.9). Value = long-term reversal in many cases. Losses cluster in liquidity crises (autumn 1998, autumn 2008, quant meltdown August 2007), when levered arbitrageurs de-lever and cheap assets get cheaper.
- 12.5: value is "short a structural break"; use stop-loss or caps on position size (examples: railroads, equity yield below bond yield after 1958, long-bond yield decline from 1980s).
- 12.6: value and momentum are negatively correlated (great complements); "when value and momentum clash, value almost always loses first". Value overlaps with carry (dividend yield), long-run reversal and low volatility; short-term reversal and pairs trading are market-making (liquidity provision), not value; quality and net share issuance are largely uncorrelated with value, but correlations among quant strategies rise from common positioning.

### Ch 13 - Currency carry (13.1-13.6)
- 13.1: UIP says high-yield currency should depreciate by the yield gap; empirically it did not (forward rate bias, known since late 1970s). NZD yields averaged 9.5% vs USD 5.5% (1983-2009), yet NZD mildly appreciated.
- 13.2 Baseline G10 carry: each week rank 10 currencies (USD, CAD, AUD, NZD, JPY, EUR, GBP, CHF, SEK, NOK) by short-term interest rate; long top 3 at weights 50/30/20, short bottom 3 at 50/30/20. 1983-2009: 6.1% annual excess return, 10.5% volatility, Sharpe 0.61; each decade Sharpe 0.58-0.63; 1994-2006 Sharpe above 1; 1953-1982 simulated Sharpe 0.51 (Lustig-Verdelhan). Drawdowns: -36% (2008), -28% (1993), -26% (1986). Rolling 3-year Sharpe between -0.5 and 2. Pre-cost; costs from bid-ask spreads in the 2000s cost at most 0.1 Sharpe.
- 13.2 Variants: top-1 vs bottom-1 gives 8% return, 16% vol, Sharpe 0.51; top-5 vs bottom-5 gives 4%, 7% vol, Sharpe 0.62 (diversification beats strongest-signal concentration). Weekly, monthly or quarterly rebalancing gives the same result (Sharpe changes at most 0.05); deposit maturity 1w/1m/3m barely matters. Real-rate carry: Sharpe 0.47; carry divided by trade-weighted volatility: Sharpe 0.70. Inverse-volatility sizing improves Sharpe; sizing by signal strength does not help.
- 13.2: dynamic re-ranking captures about double the return of a static (fixed currency pair) carry portfolio, i.e. the predictive power lives in time variation of yield spreads.
- 13.3 Emerging-market carry (15 currencies, 1994-2009): 16.4% excess, 12% volatility, Sharpe 1.30 (benign sample, higher costs); inflation was an even better signal in that sample (disinflation), no hyperinflation case in the universe.
- 13.3 Combine with: value (PPP), momentum or stop-loss, yield changes. Seasonal: carry strategy averages about 2% in January vs 0.5% in other months (last 30 years); January return negative in only 4 years since 1976 (1992, 1995, 1998, 2008), each followed by worse drawdowns later in the year; a rule "double size in January, halve for the rest of the year if January was negative" lifts Sharpe 0.6 to 0.8 (data-mining caveat).
- 13.3 Regime: when the past month's carry loss is in the worst decile, next-week return is -3% annualized vs +8% otherwise; a top-decile one-month rise in implied FX volatility predicts -7% annualized next week; short-term persistence of carry losses, so a stop-loss helps. Footnote 4: this reverses at multi-month horizon (risk-aversion episodes are short-lived).
- 13.4 Why it works: risk premium for negative skew and bad-time losses (worst months: Oct 1987 -11%, Oct 2008 -11%, Oct 1998 -9%); crash is partly endogenous (positions built slowly, unwound fast when leveraged funding hits constraints); carry beta to equities rose from 0.1-0.2 to about 0.5 by 2007-2009 ("alpha morphs into beta" with crowding). Crash hedged by options still earns positive returns, so skew risk is not the whole story. Cost of left-tail hedging was cheap in FX (carry return falls 3.0% to 1.6%) vs equities (7% to -5%) in 1987-2009 (Burnside et al.). Implied skew predicts future realized skew with the wrong sign (insurance cheap after good times).
- 13.4: peso problem and expectation errors: survey forecasts of depreciation do not materialize; a hyperinflation case (Argentina 2002) can wipe out a mechanical top-1 carry trade, so screen the universe and cap country positions.
- 13.5 Carry everywhere: cross-country bond carry (long duration where curve is steep) Sharpe near 1, EM FX carry near 1, G10 FX 0.7, credit carry only 0.3 (1993-2009); vol-weighted composite Sharpe 1.1 but lost half in 2007-08. Within-country carry (credit) is crowded and structurally overpriced; cross-country carry was less crowded. Best diversifiers are trend following and anti-risk positions.

### Ch 14 - Commodity momentum and trend following (14.1-14.6)
- 14.1: momentum works in 3-12 month windows nearly everywhere; very short (a week or less) and very long (2-5 years) windows show reversal.
- 14.2 Erb-Harvey (Dec 1982-May 2004): monthly, long 4 best / short 4 worst 12-month commodities: Sharpe 0.55; long all positive-return and short all negative-return commodities (trend-following, time-series): Sharpe 0.85. Ilmanen's 1990-2009 data: timing composite Sharpe near 0.8, ranking composite 0.5; timing does better in years when all commodities trend together (1998, 2008 down; 2003, 2007 up).
- 14.2 Signal types (return, moving average, crossover, exponentially weighted, breakout/filter, consistency) - none systematically better; moving average ratio equals a declining-weight average of past returns. Many trend followers diversify across window lengths and trade more often than monthly.
- 14.2 Volatility weighting: raises Sharpe 0.1-0.3 in every variant; without it natural gas (48% vol vs gold 16%) dominates rankings and dollar-neutral long/short is directionally biased. Volatility targeting over time mildly helps.
- 14.2 Example: nine futures (3 energy, 3 metals, 3 agriculture), long or short one unit of nearby for the next month by sign of price minus 12-month moving average: 11% excess return, 14% volatility, Sharpe 0.8, pre-costs and fees, includes roll return. MLM commodity trend index only 0.3 Sharpe since 1990 vs 0.6 for his own version (difference unexplained). Works best in energy and wheat; only silver lost. Composite Sharpe between 0.5 and 1.0 for MA windows from 3 to 12 months; weekly instead of monthly trading or a 1-2 day delay changes little pre-cost; costs reduce Sharpe by at most 0.1.
- 14.3 Tweaks: momentum stronger in less liquid assets with high information uncertainty and poorly anchored prices (energy), with disposition effect (capital gains overhang). Seasonality: momentum/trend strategies earn most in December (commodity momentum 1.6% in December vs 0.4% in January) - opposite of carry/risk-seeking (January); explained by tax-loss selling and window dressing. Trend performs better after low-volatility periods and when volatility rises; commodity momentum was up in 9 of the 10 worst S&P 500 months since 1990 (crisis alpha). Event run-up: trend following has unusually high Sharpe in the week before scheduled announcements (bonds before payrolls, oil before OPEC meetings, agriculture before supply/demand reports) because traders get cautious and losing-side traders capitulate (Ilmanen-Byrne 2003).
- 14.4 Why: behavioral underreaction and extrapolation; theory of storage (inventories): Gorton-Hayashi-Rouwenhorst 1969-2006 long-short excess returns: momentum 13.4% (t 4.9), roll 10.2% (t 3.7), inventories 8.1% (t 3.2); roll and momentum are correlated (winners tend to be backwardated). CFTC hedger/speculator positioning has little predictive power. Trend-following payoff resembles a long straddle ("long gamma, not long vega"), which makes high historical returns puzzling (long-vol should earn low).
- 14.5 Other assets: Moskowitz-Ooi-Pedersen: simple trend rule profitable on all 58 liquid futures; Ilmanen's 1-year moving-average on about 15 liquid assets per class (bonds, currencies, equity indices, commodities, vol-weighted, 10% vol target per class, 1993-2009): each class Sharpe 0.7-1.0, composite Sharpe 1.4 at 6% volatility (pre-costs). Real CTA indices realize Sharpe below 0.5. Novy-Marx: the predictive information is in returns from 6 to 12 months ago, not the most recent months. G10 FX trend lost money with short windows in the 2000s; EM FX trend stayed profitable; cross-country bond momentum fails (reversal), directional bond trend works.
- 14.5 Equity momentum box: winners beat losers by about 1% a month; skip the most recent month (reversal); one-month reversal larger for illiquid stocks and in high volatility; industry momentum works also short horizons; lead-lag from liquid core markets to neglected peripheral ones; weakens after Regulation FD (2000); momentum crash in spring 2009 (junk/value rebound); a calendar periodicity: return 12 months ago has strongest relation to this month's return, then 6, 9, 24, 36... months.

### Ch 15 - Volatility selling (15.1-15.6)
- 15.1: selling index volatility is "the archetype of selling lottery tickets that pay in bad times"; negative skew and loss timing justify a premium and make Sharpe ratios misleading; strategy had high Sharpe between the 1987 and 2008 crashes (peso problem). Straddle buy-and-hold is a gamma bet, delta-hedged straddles or variance swaps isolate implied minus realized variance; delta hedging a short option is "buy high, sell low".
- 15.2: Implied volatility of S&P 500 exceeded realized by about 4 points on average (20% vs 16%) over 24 years; typically 2-4%; other equity indices similar; single stocks about zero. Covered call writing (BXM/BXY indices) on ATM calls (beta about 0.5): half of return from equity premium, half from vol premium; 1994-2005 each about 24 bp a month; correlation with equity nearly 1 on down moves; short-dated options have wider IV-RV gap; OTM writing has more equity beta. PUT index (collateralized put selling) best return statistics, worst tail statistics.
- 15.2 Coval-Shumway: selling ATM index straddles weekly returned 3% per week, Sharpe 1.2, but bid-ask about 5% of an ATM straddle, benign sample, leverage and hidden beta. Broadie-Chernov-Johannes (1987-2005): long ATM puts average -30% a month, OTM puts -45% to -57%; Sharpe near -1 for buyers. The Merrill Lynch variance-selling index lost 12 years of excess return in under two months in autumn 2008; realized vol exceeded implied only in 1987 and 2008.
- 15.3: correlation premium: index options rich vs single-stock options, so selling index vol and buying constituent vol (dispersion) was profitable (Sharpe about 3 for correlation selling vs 1.5 for variance selling over a 13-year sample incl. 2008, probably overstated because of synthetic quotes; Driessen et al. only 0.73), but loses when correlation spikes. Skew premium: OTM index puts and OTM single-stock calls are most overpriced (Ni: OTM calls about -30% a month on mid prices; high-skew quintile -21% a month). Timing overlay: do not sell vol when implied is well below its average or below recent realized/GARCH-predicted vol. Selling is more profitable on volatile stocks and past losers (Cao-Han: covered calls on high-vol stocks earn 2% a month more).
- 15.4: explanations: systematic variance/jump/correlation risk (Carr-Wu), end-user demand pressure (end users net long index options, net short single-stock options; demand for OTM index puts and OTM single-stock calls), peso problem. Market makers cannot hedge perfectly and need compensation. Broadie et al.: standard models can explain much of the negative put returns; ATM straddle losses (-15% a month) are harder to explain and need jump premia and frictions.
- 15.5: other assets: implied above realized by 4% (crude) and 3% (natgas) 1996-2006; Sharpe of short variance swaps 0.59 oil, 0.35 gas (vs 1.02 equity index); short interest-rate vol Sharpe 0.0-0.8.

### Topic tags
- trend: ER 14. Sign of price minus 12-month moving average, volatility-weighted, monthly rebalanced, diversified across asset classes: Sharpe 0.8 (commodities, 9 futures), composite 1.4 across four asset classes (1993-2009, pre-cost). Best information in months 6-12 back; works in crises; short windows decayed in G10 FX; real CTAs below 0.5. Equity-index and EM FX trend still worked. Single-asset trend Sharpe only 0.0-0.5; breadth is where the Sharpe comes from.
- breakout: ER 14.2 treats breakout/acceleration and filter rules as one of several equal-performing trend variants; no systematic edge over moving average or return signals.
- mean-reversion: ER 12.5-12.6, 14.1. Value = long-term reversal (5-year past return as value proxy); short-term (week, month) reversal is liquidity provision; relative-value arbitrage profits faded in the 2000s; mean reversion is "short a structural break", so cap positions or use stops.
- momentum/oscillators: ER 14.5. 12-1 month momentum; skip the last month; periodicity at 12, 24, 36 months; crash risk after bear-market rebounds; momentum performance not itself positively autocorrelated.
- patterns: not covered.
- intraday/sessions: not covered (weekly or monthly horizons only). Only event run-up (ER 14.3).
- seasonality/time: ER 12.3, 13.3, 14.3, 11.4. January: value premium (2.2% vs 0.24% per month, US 1926-2008) and FX carry (about 2% vs 0.5%); December: momentum/trend (1.6% vs 0.4% for commodities), hedge funds. Event-week run-up for trend (before payrolls, OPEC, supply/demand reports). Year-end window dressing. Seasonal commodity backwardation before harvest (11.3).
- volatility: ER 15. Index IV above RV by 2-4 points (S&P 20 vs 16); single stocks about zero (correlation premium); skew premium in OTM puts; FX carry crash signals from implied vol jumps; volatility weighting of signals and sizes (Sharpe +0.1-0.3); trend does better after low vol.
- stops-and-exits: ER 12.5, 13.3 (stop-loss on carry: after worst-decile monthly loss, next week is -3% vs +8% annualized), 14.4 (trend following equals stop-loss discipline). Cap or stop for value positions (structural breaks).
- position-sizing/risk: ER 13.2, 14.2. Inverse-vol sizing improves Sharpe for carry and trend; sizing by signal strength does not help carry; diversification across signals beats strongest-signal concentration (carry top-5/bottom-5 Sharpe 0.62 vs top-1 0.51); top-3/50-30-20 weights.
- testing-and-robustness/overfitting: ER 11.4, 12.1, 12.3, 13.4. Bias taxonomy (survivorship, backfill, selection, liquidation, lookback, lookahead); benign-sample/peso problem; style timing and refinements overfit; deliberately naive indicators (AMP 2009) as anti-overfitting; Sharpe overstates strategies with negative skew; strategies "morph from alpha into beta" as they get crowded; t-statistics from sorted long-short portfolios (13.4% momentum t 4.9).
- costs/execution: ER 13.2, 14.2, 15.2. Pre-cost results throughout; FX carry costs 0.1 Sharpe at most (low turnover); momentum has higher turnover than value or carry; slower signals better after costs; straddle bid-ask about 5%; CTA gross-to-net gap (5.4% to 0.9%).
- psychology/discipline: ER 13.4, 11.4. Return chasing (investors lose 3-7% a year vs buy-and-hold in hedge funds); crowding; carry traders' complacency; "up by the stairs, down by the elevator".
- portfolio/diversification: ER 12.6, 13.5, 14.5. Value and momentum are negatively correlated; trend is the best diversifier of carry and value (carry/value/vol selling are all "short volatility", trend is "long volatility"); composites of carry in many markets still crash together (lost half in 2007-08).

### Testable ideas

1. ★ **Cross-sectional FX carry on FTMO FX pairs** - each week (or month), rank the available FX majors/crosses by interest-rate differential (short-term policy rates, or the CFD swap points as a carry proxy), go long top 3 and short bottom 3 with 50/30/20 weights, vol-scaled; exit at next rebalance; optional stop: flat for a week after a worst-decile monthly carry loss. Source: ER 13.2, 13.3. Evidence: G10 Sharpe 0.61 (1983-2009, pre-cost), 6.1% a year, 10.5% vol, drawdown -36% in 2008; Sharpe 0.7 with carry/vol. Fit: the swap cost on FTMO is exactly the carry we want to earn, so we must test with the real broker swap (long high-yield currency pays/earns the swap per symbol and day). Poor-to-medium: FTMO swap includes broker markup and triple-swap Wednesdays and is in practice already near the interest differential minus a spread, which may eat the edge; but turnover is very low, so the spread cost is small. Differs from failed families: this is a carry/holding-flow strategy, not price pattern; the edge is the interest differential itself. Need a rate table (FRED short rates are available).

2. ★ **FX carry January and stop-loss overlay** - take idea 1 (or a simpler 3-vs-3 basket) and test (a) the January seasonal (double weight in January) and (b) after a January with negative carry return, halve exposure for the rest of the year; (c) weekly stop: go flat for a week after the worst decile of one-month carry returns or after a top-decile one-month rise in a volatility proxy (use realized FX vol or VIX). Source: ER 13.3. Claim: Sharpe 0.6 to 0.8 (author flags data-mining). Fit: tiny sample (one trade-year per year, perhaps 10-16 Januaries in our data); must pre-register and is under-powered for t >= 3; treat as a secondary check, not a standalone test. Differs from failed families: time-of-year regime filter on a carry book.

3. ★ **Time-series trend on commodity futures with volatility weighting (EIA contracts 1-4 plus CFD oil/gold)** - monthly: long if price (front contract, roll-adjusted excess return series) is above its 12-month moving average, short if below; position sized inversely to past-year volatility, per-asset vol target; also try a ranking version (long top 4 / short bottom 4 on 12-month return). Source: ER 14.2. Claim: commodity composite Sharpe 0.8 (11% return at 14% vol, 9 futures), ranking Sharpe 0.5, Erb-Harvey 0.55/0.85; breadth across 15 assets per class and four classes gives 1.4 (pre-cost). Fit: poor to medium for CFD-only trend (our failed family: "CFD trend following"); the difference to try is correct roll-return accounting and carry-aware construction using EIA contracts 1-4 (term structure) and combining with idea 4. Our data has few commodities (energy contracts 1-4, gold, oil CFDs), so breadth is low; real value is as a test of whether the dead CFD trend result is due to missing roll/carry in prices. Overnight positions pay CFD swap.

4. ★ **Commodity roll-yield / term-structure carry (EIA energy contracts 1-4)** - monthly: compute roll yield from slope between contract 1 and 2 (or 1 and 4) for crude, natural gas, heating oil, gasoline; long the most backwardated, short the most contangoed (or long/short each by sign of slope), hold one month. Source: ER 11.3, 14.4. Claim: roll and momentum long-short strategies earned 10.2% (t 3.7) and 13.4% (t 4.9) 1969-2006 across about 30 commodities; commodities with positive roll earn positive excess returns, aggregate backwardation predicts higher near-term returns (Hong-Yogo); roll and momentum overlap through inventories. Fit: good in principle (we have per-contract energy data), poor in breadth (only 4-5 energy markets; Ilmanen's own sample was dominated by an energy bull market, which he calls too-good-to-be-true); risks: GSCI roll idea and VIX basis already spent; this one is different because it is cross-sectional carry rather than index-roll flow timing. Test also the "storage" link: add the inventory proxy (EIA inventory data if available) as a conditioning variable.

5. ★ **Cross-asset 12-month trend with vol targeting on liquid futures-like series we have (indices, Treasuries, FX, gold, oil, crypto perps)** - monthly: sign of 12-month return (skipping nothing), each asset scaled to 10% vol, equal risk across asset classes; also the Novy-Marx variant using only the return from month -12 to month -6 (or -12 to -2). Source: ER 14.5. Claim: asset-class Sharpe 0.7-1.0, composite 1.4 pre-cost; only 6% composite volatility. Fit: medium. Breadth is our constraint (about 34 CFDs but many correlated); costs on monthly turnover are small, and the swap on longs/shorts is a known cost. Differs from failed families: slow (monthly), vol-scaled and cross-asset diversified, versus the faster trend/breakout CFD rules that died on costs; the likely outcome is a falsification, but it cheaply closes the question for slow trend. Should test crypto perps separately, where funding is the carry.

6. **Equity value / sector-neutral value on US shares (Alpaca daily bars)** - needs fundamentals, which we do not have (only prices). Price-only substitute: 5-year past return reversal (AMP value proxy), skipping the last year, long bottom decile / short top decile within sector, monthly. Source: ER 12.5, 12.6. Claim: all AMP strategies Sharpe positive 0.1-0.9; naive 5-year reversal as value proxy. Fit: poor-medium (no fundamentals; the cost of shorting small caps; reversal over 3-5 years needs history, but our shares only start in 2015, so only 5 years of lookback fits in about 6 years of test; underpowered). Not a priority.

7. **Value + momentum combination within shares (two-signal composite)** - rank US shares by 12-1 momentum and by price-based value proxy (e.g. distance from 5-year average price) with equal weight; long/short quintiles, monthly. Source: ER 12.6. Claim: value and momentum negatively correlated, combination sharply raises Sharpe. Fit: medium for momentum leg (Alpaca daily); the value leg is weak without fundamentals. Differs from failed families: cross-sectional equity factor, not CFD price pattern. Low priority because of data limits and short history (2015+, 6 years of reversal lookback).

8. ★ **Event-week run-up trend (pre-announcement trend continuation)** - trade in the direction of the past 1-3 month trend during the 5 trading days before a scheduled event (US payrolls for Treasury futures/yields, OPEC meetings or EIA inventory reports for oil, FOMC for FX/indices); hold until the event, exit before the release (no event exposure). Source: ER 14.3 (Ilmanen-Byrne 2003). Claim: abnormally high Sharpe for trend following in bonds in the week before payroll reports; same for oil before OPEC and agriculture before USDA reports; mechanism: traders de-risk before the event, losing side capitulates. Fit: good in terms of data (daily Yahoo 10-year futures, EIA energy, FRED, FOMC dates are known; weekly holding, no overnight costs beyond a few days). This is a calendar-driven positioning effect with an actual mechanism (risk reduction before scheduled events), not a price pattern; the claim is from one study, so needs a pre-registered, power-checked test. Differs from failed families: event calendar, not intraday session rule or month-end flow.

9. **Treasury/FX carry via yield-curve slope (cross-country bond carry)** - long duration in countries with the steepest curve, short in flattest; we only have US yields from FRED and Yahoo 10-year futures, so cross-country is not possible; the time-series version "long Treasuries when the curve is steep (carry), flat otherwise" is testable on FRED. Source: ER 13.5. Claim: cross-country bond carry Sharpe about 1 (1993-2009). Fit: poor for the cross-country form (no foreign data); medium for the US time-series form; low power (monthly, one market). Possibly combine with the spent month-end duration extension as a conditioning variable.

10. **Volatility risk premium via VIX futures/ETF carry** - short front VIX futures (or long VIX term-structure roll-down) sized by realized volatility, with a rule "do not sell vol when implied is well below its normal level, recent realized or GARCH-predicted vol". Source: ER 15.3. Claim: implied minus realized about 4 vol points on S&P (1986-2009), selling Sharpe 1.0-1.2 before crashes, but one crash can erase 12 years of gains (ML index). Fit: VIX basis is already spent in our families; the new element would be the timing overlay and the sign of the IV-RV gap using realized S&P vol versus VIX (we have Cboe VIX futures and index CFDs). Fat-tail and gap risk makes it a bad fit for prop-firm rules (goal 1); only for goal 2 with strict loss caps. Do not repeat the VIX basis test, only the overlay if the old result is kept.

11. **Crypto perp funding carry (analogy to FX carry)** - sort Binance perps by funding rate; long the lowest funding (receive, or pay least), short the highest funding (receive funding), delta-hedge with BTC; weekly. Source: transfer of ER 13.2/13.5 (carry in every market is a premium for bearing crash risk) and ER 13.4 (crowding turns alpha into beta; crash when leveraged funding hits constraints). Evidence in book: carry strategies in all markets Sharpe 0.3-1.3 with crash risk. Fit: good (funding data available), relates to the already-passed taker-flow sort (Strategy 20), so test as a combination or conditioning signal. Differs: carry (funding) instead of flow; the book's warning that carry crashes are short-lived and persistent over a week (worst-decile month followed by negative week) can be used as a stop test.

12. **Short-horizon carry crash stop (generic overlay)** - for any carry book (FX carry, funding carry, term-structure): go flat for the next week after the worst-decile one-month loss of the book, or after a top-decile jump in an implied/realized volatility measure. Source: ER 13.3. Claim: next-week return -3% (after worst-decile month) vs +8% annualized otherwise; implied vol jumps: -7%. Fit: good as an overlay with daily data; low power (decile events are rare, correlated), so use as an exposure-scaling rule tested in-sample only once with pre-registered parameters.

### Warnings / pitfalls
- Almost every performance number in these chapters is pre-cost and pre-fee; the author only says costs reduce Sharpe by "at most 0.1" for slow signals (carry, 12-month trend) and notes momentum and short-horizon signals are much worse. Real CTAs earn Sharpe below 0.5 whereas his simulated trend gets 0.8-1.4 (ER 14.2, 14.5): treat simulated Sharpe as an upper bound.
- Hindsight in universe choice (G10 list picked with hindsight, excluded hyperinflated currencies) and benign samples (Great Moderation, an energy bull market, post-1994 emerging markets) inflate results; "the 1990-2009 energy bull market" is explicitly called a "too-good-to-be-true" sample.
- Negative-skew strategies (carry, vol selling, value) look best until the crash; Sharpe understates risk; the strategy's long-run Sharpe above 1 in the mid-2000s "was never sustainable" (ER 13.4). Measure skew, worst months, and loss timing; use at least one crisis in the sample.
- Hedge-fund style reporting biases (survivorship, backfill, selection, liquidation, lookback, lookahead): net bias 6.6% a year in equal-weighted HF indices; applies in spirit to our trial ledger (only reporting winners, backfilled variants).
- Alpha becomes beta as strategies crowd (carry beta rose 0.1-0.2 to 0.5); August 2007 quant meltdown and 2008: crowded strategies lose together when leveraged holders de-lever; correlation among "uncorrelated" quant strategies rises.
- Style timing and refinements are the most overfit-prone part (author's own caution): January doubling rule, value spread, regime indicators "fitted to previous crash episodes", false alarms. Regime indicators tend not to be robust across episodes (1997-98 EM origin vs 2007-08 US origin).
- Stale or smoothed prices (real estate, hedge funds, PE) understate volatility; check autocorrelation of any series before computing Sharpe.
- Roll-return accounting: always use proper excess return series; a generic nearby price series ignores roll (oil flat in price, -36% in excess return over two years).
- Value and mean-reversion strategies are short structural breaks; use caps or stops; "this time is different" can be true (equity yields below bond yields after 1958; Japanese bonds, "the widowmaker").
- Carry in one country can collapse via hyperinflation (Argentina 2002): screen universe, cap per-country exposure.
- Diversifying carry across more asset classes crystallizes rather than diversifies the common crash exposure (composite lost half in 2007-08); trend following is the better diversifier.
- Momentum has high turnover and costs; trend following returns themselves are not momentum (rare exception); momentum crashes on sharp reversals after bear markets (1932, spring 2009).

# Part 4: ch.16-21: growth, inflation, liquidity and tail factors, feedback effects, forward-looking measures


Citation note: the extracted text has no printed page numbers, so cites are chapter.section (ER 16.4.1 etc.).

### Overview
- This part moves from asset-level and strategy-level return sources (earlier chapters) to the underlying factors behind them: growth (ch 16), inflation (17), liquidity (18), tail risks = volatility, correlation, skewness (19). Ch 20 covers endogenous feedback effects (crowding, momentum then reversal, liquidity spirals). Ch 21 covers forward-looking value and carry indicators and a building-block view of expected returns. Ch 22 (carry interpretation) only starts at the very end of the range.
- Stance: a value-minded, risk-premium-plus-behavioral eclectic. He is agnostic whether each premium is rational compensation or mispricing. He stresses that most "premia" are paid for losing money in bad times (illiquidity, carry, vol selling, betting against beta) and that premia vary over time: widest right after a stress event, thinnest after a long calm and a crowded inflow.
- The material is macro/strategic and monthly or longer. There are almost no tradable daily rules and no cost-net backtests. Its main value for us: (1) which counterparty pays and why (leverage-constrained buyers of high-vol assets, lottery buyers, forced de-leveraging, delegated managers), (2) honest-testing lessons (peso problem, smoothed returns, premium decay after publication, microstructure bias), (3) a few cross-sectional sorts that are testable on our US-share daily data and crypto perps.
- Almost all numbers are US data, monthly, 1990-2009 or long history, gross of costs unless stated. Nothing here is net of modern costs.

### Chapter notes

### Ch 16 - Growth factor (16.1-16.6)
- 16.1 Table 16.1 correlates 15 assets/strategies with monthly changes in four factor proxies (consensus next-year GDP growth, consensus inflation, BoE liquidity index, VIX), 1990-2009. Risky assets load on growth; only trend/momentum, value and long Treasuries diversify growth risk. All risky assets lose when illiquidity or VIX rises; momentum strategies diversify those times. Contemporaneous, not predictive. Factor rankings are similar across the four factors (one "risk-on/off" factor explains much, especially after 2008).
- Characteristics vs covariances: empirically the characteristic (book/price, size, illiquidity) tends to carry more premium than the covariance with the factor. Argues for behavioral stories; rationalists say the characteristic proxies for noisy beta.
- 16.2-16.3 Growth is mostly priced into valuation, not into expected returns. Fast growth does not mean high returns: growth stocks underperform value stocks (overpriced growth); across countries 1900-2009 GDP-per-capita growth did not raise real equity returns; China 1993-2009 had ~10% real GDP growth and a slightly negative USD equity return; Asia ex-Japan grew about 3x faster than other regions with unexceptional equity returns. Reason: dilution. Emerging market cap grew 13.1% a year but holders got 3.2% price return (5.4% total) over 11 years (Speidell et al.); US dilution ~2%.
- Of ~3% aggregate real earnings growth over 60-80 years, existing shareholders got only ~1% (real EPS growth); about 2% was diluted by new issuance. Trend EPS growth (<2%) has been a ceiling, not a floor, relative to GDP (>3%). Market cap growth is not investor return.
- 16.4.1 Aggregate: equity returns lead next-year GDP growth (US correlation +0.24 since 1926), not the reverse. At firm level positive earnings surprises give price jump plus post-announcement drift. At aggregate level the contemporaneous earnings-return link is negative (forward-looking prices). Cumulative binary growth-surprise index (actual vs consensus, +1/-1) tracked US equities well since the mid-1990s (Fig 16.3). Monthly equity return vs change in consensus growth forecast: +0.33.
- Footnote 3: good growth/employment news lifts stocks when slack is large, hurts stocks late in an expansion (rate hike fear). The sign of the reaction to the same data is cycle dependent.
- 16.4.2 Yield curve slope predicts GDP growth; inversion preceded every US recession since 1960 (one false signal in 1967, 2005-06 inversion had an unusually long lag to Dec 2007). Curve vs equities as a growth predictor: curve better in 1950s-80s (0.56), equities better since the 1980s (0.46 vs 0.13). Zero lower bound breaks the relation.
- 16.5 Risky-asset expected returns are countercyclical in return regressions, but investor surveys show procyclical subjective expectations (optimistic at peaks).

### Ch 17 - Inflation factor and premium (17.1-17.4)
- Long nominal Treasuries have the most consistently negative inflation beta; the inflation risk premium (IRP) is the main driver of the bond risk premium (BRP). BRP was 3-4% in the early 1980s, near zero in the 2000s. IRP is level dependent (higher inflation, higher inflation uncertainty) and higher when inflation coincides with recession (stagflation, supply shocks).
- Commodities (energy especially) and linkers are the best inflation hedges; stocks have negative short-term but positive long-term inflation beta (5-year returns, 200 years of data). P/E has a "sombrero" shape vs inflation: highest at low positive inflation, lower at both high inflation and deflation. Deflation is the worst regime for almost all assets except nominal government bonds.
- Gold: does well in disinflation and turmoil, not a clean inflation hedge; inflation disagreement predicts gold returns better than inflation level.
- TIPS lesson (17.3): early TIPS looked cheap (break-even inflation 1.2% vs survey 2.7%, measured IRP -1.5%) because of a novelty/illiquidity premium; it faded as the market matured, then spiked again in fall 2008 (BEI collapsed to ~0). BEI averaged 1.75% and ranged 0-3% while the consensus 10-year inflation forecast stayed in 2-3%. BEI moves reflect liquidity more than inflation views.
- Inflation process: persistence, uncertainty and level all rose to 1980 then fell; investors under-predicted inflation in the 1960s-70s and over-predicted in the 1980s-90s (learning, not necessarily irrational). The stock-bond correlation sign flips with the regime (positive in the 1970s-80s, negative since late 1990s, more negative with low inflation and flight to quality).
- Ref: Fig 17.7 average monthly returns when the inflation factor is above/below median (1990-2009): commodities gain most, long Treasuries lose most.

### Ch 18 - Liquidity factor and illiquidity premium (18.1-18.5)
- Four meanings of liquidity: monetary, balance-sheet, funding, market. Market liquidity facets: tightness (spread), depth, resilience. Proxies: bid-ask, Amihud ILLIQ (average absolute daily return divided by dollar volume), turnover, zero-return days, return reversal induced by order flow (Pastor-Stambaugh).
- 18.2 Trading costs fell 4-5x since the mid-1970s (Hasbrouck effective cost, 1926-2005; small caps always costlier; peak in the 1930s). Market illiquidity is countercyclical and rises before recessions (Naes et al.). US turnover: >100% late 1920s, ~10% 1940-70, >200% in 2007. Liquidity and funding feed each other (Brunnermeier-Pedersen spirals); liquidity regimes are close to two-state (flush or absent).
- 18.3 Cross-section of stocks: less liquid stocks earn higher gross returns (Amihud-Mendelson). Low past turnover beats high turnover (Chen-Ibbotson-Hu); high-turnover small caps do especially badly (lottery tickets). Liquidity beta (Pastor-Stambaugh 2003): high-beta minus low-beta decile earns +7.5% a year (four-factor adjusted), with a moderate loss in 2008. Acharya-Pedersen: expected illiquidity difference worth ~3.5% a year between liquid and illiquid stocks, liquidity betas ~1.1% more. Illiquid stocks are small-cap value, low price, high liquidity beta.
- Short-term reversal (stat arb) is a liquidity-provision return: buy recent losers, sell recent winners. Gross profits are higher in high-VIX, high-turnover, low-return periods (Nagel 2009, Rinne-Suominen 2010) but declined over time; today only very cost-efficient players keep a net profit. Premium for illiquidity decayed over time (Ben-Rephael et al.), premium for liquidity risk less clearly.
- Other assets: corporate bond illiquidity premium ~45 bp long IG, ~100 bp HY (average); ~10 bp IG / 30 bp HY in another study, ~100 bp for HY in stress regimes. Value strategies lose and momentum strategies gain during liquidity droughts (Asness-Moskowitz-Pedersen 2009). Hedge funds with higher autocorrelation (smoothing) and lockups earn more. PE: 7-12% higher annual returns when aggregate liquidity improves; restricted stock discount 20-30%.
- 18.4 Time variation: the liquidity premium (Watanabe-Watanabe) is ~5% per month in a rare "high liquidity beta" state (under 10% of time, disproportionately in January) and ~0 otherwise. Small caps and corporate bonds tend to outperform in January (year-end liquidity). Jensen-Moorman: least-liquid quintile beats most-liquid by 0.9% a month on average; 2.3% when Fed policy is easy, 0.3% when tight. Aggregate illiquidity mildly predicts higher medium-term market returns, stronger combined with volatility or value, stronger for small caps. Premiums were widest after 1998 and 2008 and thinnest 2005-07 when "be like Yale" capital crowded in. Recommendation: opportunistic, contrarian liquidity provider; save ammunition in good times.
- Footnote 1: illiquid assets' Sharpe ratios are overstated (stale prices, smoothing, uncompensated liquidity risk cost).

### Ch 19 - Tail risks: volatility, correlation, skewness (19.1-19.7)
- Not all volatility is equal. Across asset classes risk and return are mildly positive; within asset classes the relation is flat or negative: high-vol stocks lose to low-vol stocks, longest bonds and CCC credit disappoint.
- 19.3 Idiosyncratic/total volatility sort (Ang et al. 2006, 2009; daily returns of the past month): quintile 5 minus quintile 1 about -1% per month raw, -1.2 to -1.4% alpha, works in all G7 markets. Sample 1963-2000; 2000-2009 reversed for broad universe (small-cap high-vol rallied in 2003, 2009), weaker in large caps (Blitz 1986-2009), fades when value-weighted, ex-small-caps or size-controlled. Stronger in small caps (costs can eat it), stronger where retail dominates, flips positive where institutions dominate; partly short-term reversal, partly low subsequent earnings, partly microstructure (bid-ask bounce). Long windows (3 years) with monthly data give a positive sign; short-run vol is rewarded negatively, long-run vol positively (Cao-Xu).
- Hockey-stick shape: only the top quintile (highest recent vol, highest upside vol, highest MAX daily return, highest expected skewness) underperforms; quintiles 1-4 are similar. MAX (Bali-Cakici-Whitelaw 1962-2005): highest decile of last-month maximum daily return underperforms lowest by about 1% per month, robust to controls, subsumes idiosyncratic vol and skewness. Expected skewness (Boyer-Mitton-Vorkink): Q5 minus Q1 raw 0.67% per month, 3-factor alpha 1%; predicted by lagged idio vol, small size, negative momentum, industry. High-vol and high-skew stocks outperform in January (Doran-Jiang-Peterson), underperform more when sentiment is bullish.
- Information moves slowly between options and stocks (Ang-Bali-Cakici): stocks with rising call implied vol beat falling by ~1% next month; Cremers-Weinbaum: stocks with expensive calls vs puts (put-call parity deviation) beat the reverse by ~50 bp per week. Option data not available to us.
- Volatility factor: stocks with larger negative sensitivity to rising vol earn a premium (small-cap value ~0.5% per month, Moise); weaker than the vol-characteristic effect. Treasuries became VIX diversifiers only after ~1998; momentum and value were safe havens in 1990-2009; stat arb may work better in high-vol regimes.
- Market timing with vol: contemporaneous return-vol correlation is strongly negative (leverage and volatility feedback), predictive relation weak or negative next month, more positive at 2 months (delayed feedback). Average stock correlation positively predicts next-quarter market return, average variance does not (Pollet-Wilson). Implied-minus-realized variance gap (variance risk premium, intraday realized) predicts next-quarter equity returns, R2 about 15% (Bollerslev-Zhou). For duration timing, carry and trend, higher vol predicts mildly lower near-term returns.
- Options and correlation: implied exceeds realized vol by 2-4 points for equity indices but about 0 for single stocks. Implied correlation averages ~50% vs realized ~30%. Correlation-selling (dispersion) earned 14% per month before costs, annualized Sharpe 3.3 (1996-2008, synthetic correlation swaps), but costs and the Oct 2008 correlation spike (>75%) caused big losses. Single-stock OTM calls: -28% per month for the top moneyness quintile vs +2% for the lowest three (Ni). CDO tranche lesson (Box 19.1): senior tranche losses occur only in the worst states, so the fair premium is large; ratings ignore states of the world.
- 19.4 Skewness: data favor positive-skew preference (lottery buying by retail, prospect-theory overweighting of small probabilities, overconfident stock pickers). Coskewness premium: low-coskew beats high-coskew by 3.6% a year (Harvey-Siddique). OTM call richest in January.
- 19.5 Why high-vol assets do badly: lottery preference plus leverage constraints. Investors who cannot lever buy high-beta assets, so these are overpriced (Black 1972; Baker-Bradley-Wurgler: delegated managers, benchmark pressure, high-vol stocks have higher costs and lag in bad times 1973-74, 1987, 2000-02, 2008). Betting Against Beta (Frazzini-Pedersen 2010): long low-beta, short high-beta, each scaled to beta 1, monthly rebalanced, works in stocks, bonds, credit, FX, futures; Sharpe comparable to value, carry, momentum; turnover like value; loses when the TED spread widens (funding tightening). Falkenstein: unrelated to vol except overpaying for certainty and for dreams; status-seeking, relative risk unpriced.
- 19.6 Time variation: tail-risk premia are largest right after the loss event (speculative capital withdrawn) and smallest after long calm. Implied vol/skew/correlation lag realized values and stay high for months to years (skew became asymmetric only after the 1987 crash; FX carry skew after 2007-08). Buying vol in 2005 at low levels bled for two years.

### Ch 20 - Endogenous return and risk, feedback effects (20.1-20.4)
- Feedback loops: wealth-dependent risk aversion, leverage/margin spirals, liquidity spirals, risk-control spirals (VaR, stop-loss, portfolio insurance sell into falls). Momentum traders destabilize, contrarians stabilize; the balance between the two groups moves over time (Perold-Sharpe 1988). In 2008 value buyers did not show up.
- Fig 20.1 (1990-2009, monthly): average one-month autocorrelation of asset/strategy returns +0.20 (short-term momentum; part may be illiquidity/smoothing); correlation of the latest 6-month return with the 6-month return 18 months earlier -0.11 (reversal). Only commodity trend-following and the size effect showed mild negative autocorrelation in this window. Analyst forecasts show the same momentum-then-reversal pattern.
- Strategy life cycle (Fig 20.2): success, attention, inflow, competition erodes ex ante Sharpe while realized returns stay good, expected return can go negative with crowding, liquidation in bad times; afterward Sharpe settles positive if it was a risk premium, towards zero if it was an inefficiency. "Alpha morphs into beta." Gaps between disasters can be a decade or more (FX carry, vol selling, front-end credit, illiquidity), so benign samples understate risk.
- August 2007 quant crisis: market-neutral equity strategies moved in lock-step for days (common positions plus lost liquidity). New risk: crowded trade risk. Contrarian timing loses if entered too early or if there is a structural change. Stein (2009): quants reusing the same history create crowding, so markets need not have become more efficient. Adaptive markets (Lo): edge waxes and wanes.
- Footnotes: long-horizon reversal evidence (3-5 years) is weak with econometric problems; deviation from a value anchor is a better signal than past return; disposition effect and fund inflows create short-term momentum.

### Ch 21 - Forward-looking measures of returns (21.1-21.3)
- Value and carry indicators predict long-horizon returns even without knowing why; they are poor short-term predictors and fail if structure shifts. Equity: earnings yield (E/P), preferably 10-year smoothed earnings (1-year E/P is distorted by cyclical lows like 1932, 2002, 2009); forward consensus earnings are biased upward; dividend yield alone is too narrow because buybacks replace dividends (use payout yield). Bonds: YTM, survey-based BRP (10-year yield minus consensus average expected bills), real yield with long-term inflation expectations. Credit: OAS/CDS spread overstates the premium (includes expected default loss and embedded options); carry for levered credit needs the financing spread (LIBOR minus GC repo); money-market quote conventions differ.
- Building-block framework (Table 21.1): expected return = carry (income or return if markets are unchanged, including roll-down) + expected cash-flow growth + expected valuation change (value signal; often set to zero because mean reversion is weak). Used for apples-to-apples comparison across assets and strategies. FX carry earns nearly all profit from carry; commodity momentum has incidental carry and no value anchor.
- Start of Ch 22 (to line 19963): carry can be read as market expectation of offsetting price moves (risk-neutral, uncovered interest parity, expectations hypothesis) or as risk premium; horse races favor the risk premium reading, positive-carry strategies have been profitable in all asset classes studied.

### Topic tags

- **trend**: Short-term momentum (+0.20 monthly autocorrelation, 1990-2009) with reversal beyond a year (-0.11). Momentum strategies are liquidity-drought and VIX diversifiers. Momentum traders destabilize markets. (ER 20.2, 18.3, 19.3)
- **breakout**: nothing.
- **mean-reversion**: Short-term reversal is a liquidity-provision return, larger in high-VIX/high-turnover times, decayed over time and net-profitable only for cost-efficient players (ER 18.4). Long-term (3-5 year) reversal weak. Value-anchor deviation beats raw past return as reversal signal (ER 20.4 note 1). Stat arb may work better in high-vol regimes (ER 19.3).
- **momentum/oscillators**: nothing beyond autocorrelation statistics.
- **patterns**: nothing.
- **intraday/sessions**: nothing. Only microstructure notes: bid-ask bounce creates artificial negative lead-lag between vol and returns.
- **seasonality/time**: January effect in liquidity premium (5% per month in the rare high-beta state, concentrated in January), high-vol and high-skew stocks and OTM calls outperform/overpriced in January (ER 18.4, 19.3, 19.4); small caps and corporate bonds tend to outperform in January. Year-end liquidity. Business-cycle stage matters for growth-news response (ER 16.6 note 3). Sign of stock-bond correlation varies by inflation regime.
- **volatility**: Vol is not rewarded within asset class (hockey stick, top quintile only). Short-run vol rewarded negatively. Vol-feedback delay: next-month return vs vol is weak/negative, 2-month more positive. Implied-realized gap predicts next-quarter market return. High vol predicts mildly lower returns for duration, carry and trend strategies. Equity index implied-realized gap 2-4 points; single stocks ~0.
- **stops-and-exits**: Stop-loss and VaR rules are procyclical: selling into weakness amplifies downturns (ER 20.1).
- **position-sizing/risk**: Betting against beta is a levering-up of low-risk assets; leverage constraints are the reason the premium exists. High measured Sharpe with hidden tail risk is typical (smoothing, vol selling). Low measured vol at the peak (2007) hid the highest true risk.
- **testing-and-robustness/overfitting**: Peso problem: track records of asymmetric-payoff strategies overstate return and understate risk until the rare event. Results sensitive to research design (equal vs value weights, small caps, size control, window length, daily vs monthly returns). Published anomalies decay (illiquidity premium, liquidity-provision profits). Quant crowding from reuse of the same history (Stein). Characteristic vs covariance confusion. Contemporaneous correlations (Table 16.1) are not predictive. Market cap growth is not investor return.
- **costs/execution**: Many anomalies concentrate in small, illiquid, high-cost stocks, so gross profits overstate net (vol effect, MAX, liquidity-provision reversal, short-selling constraints on illiquid stocks keep them overpriced). Dispersion trade 14% a month gross, costs may eat much. Trading costs fell 4-5x since the 1970s.
- **psychology/discipline**: Lottery preference (retail, prospect theory, overconfident pickers), return chasing, investor-extrapolation, procyclical sentiment, benchmark-driven delegated managers, disaster myopia vs overweighting of small probabilities; contrarian positioning needs deep dislocations to be accepted.
- **portfolio/diversification**: Four-factor view (growth, inflation, liquidity, tail risk). Only trend, value and duration diversify growth; Treasuries diversify VIX shocks only since ~1998; momentum diversifies illiquidity. Strategies that look uncorrelated become correlated in crowded unwinds (Aug 2007).

### Testable ideas
Honest assessment: this part is mostly macro and risk-premium narrative. Few ideas are testable on our data at daily frequency; the ones below are the best fits. None is claimed net of costs by the author.

1. ★ **MAX / lottery-stock short-term sort (US shares daily)** - Each month (or week, to match our turnover rules) rank US shares by the maximum daily return of the past 21 trading days (and variants: past-month idiosyncratic vol, upside vol). Short or underweight the top decile/quintile versus the rest or versus the lowest decile. Hold a month. Author's defaults: 1-month window, monthly rebalance, decile sort. Source: ER 19.3, 19.4 (Bali-Cakici-Whitelaw 1962-2005: -1% per month top vs bottom decile; Ang et al. vol sort -1% per month Q5-Q1, 1963-2000). Evidence: significant and robust to controls in the original sample, weaker large caps, reversed in 2000-2009 broad universe, vanishes if value-weighted/ex-small-cap/size controlled. Fit: medium. Our universe is 23,700 US shares since 2015 with Alpaca daily bars; no borrow cost data and short-selling hard in the very names that drive it (low price, illiquid). Needs a real-share cost model and a borrow assumption; use a price and dollar-volume floor so it is tradable. Differs from failed families: it is a cross-sectional sort on a behavioral mispricing (lottery buyers + leverage/short constraints), not price pattern or intraday rule.

2. ★ **Betting against beta / low-vol minus high-vol on US shares (and a crypto-perp variant)** - Monthly: estimate beta (or total vol) from the past 1 year of daily returns (author's source uses shrunk betas), rank, long low-beta portfolio and short high-beta portfolio, each scaled to beta 1, rebalanced calendar month. Source: ER 19.5 (Frazzini-Pedersen 2010, positive Sharpe in stocks, bonds, credit, FX, commodities, comparable to value/carry/momentum). Claimed to lose when funding conditions tighten (TED spread widening). Fit: good on US shares (cheap daily data; low turnover vs 1-month vol signals); on Binance perps test whether high-beta alts are overpriced by retail leverage-seekers (a counterparty story: leverage-constrained buyers). Differs from failed families: it is cross-sectional, market-neutral, a structural leverage-constraint premium, not a CFD pattern. Check the long leg's financing and the short leg's borrow; measure with t >= 3 and the multiple-testing ledger; very large drawdown risk in 2008/2020-type de-leveraging (our sample 2015+ has March 2020).

3. ★ **Crypto-perp lottery sort (MAX and skew) with funding included** - Weekly: rank Binance perps by max daily return of the last 7-14 days (or past-week upside vol); short the top tercile/quintile, long the bottom, equal-risk weights, funding and taker fees charged. Source: transferred from ER 19.3-19.5 (lottery preference, leverage-constrained retail buy the highest-bang-for-buck assets). The book gives no crypto evidence. Fit: good data, and we already hold a weekly crypto taker-flow sort (Strategy 20); this is a different signal family but the same sorting infrastructure. High overlap risk with Strategy 20's long-short book (check correlation, since flow, funding and MAX are likely related). Funding rate itself is the cost of leverage demand; the sort could be conditioned on funding as a direct measure of leveraged lottery demand. Differs: not price-breakout; the claimed counterparty is the leverage-constrained retail speculator.

4. ★ **Short-term reversal as liquidity provision, conditioned on VIX (US shares, daily/weekly)** - Weekly sort on last-5-day return (or last-month), long the bottom decile, short the top, dollar-neutral; only trade in (or scale up with) high-VIX/high-volatility states since reversal profit rises with VIX (Nagel 2009, ER 18.4). Exit after 1 week. Evidence: gross profits large in high-vol times, but declining over time and net-profitable only for cost-efficient participants (author warns). Fit: poor to medium: weekly turnover 100%+, our real-share costs probably eat it; test only in the top VIX tercile where the signal is largest and cost per trade can be justified. Counterparty: forced sellers/buyers, funding-constrained intermediaries. Differs from failed families: cross-sectional reversal, not time-series pattern or gap fade; it is related to the failed "gap fade" idea by mechanism (overreaction), so expect overlap; mark as the riskiest of the stars.

5. **January small/illiquid/lottery seasonal (US shares)** - In the first trading days of January (or last week of December through January) go long the highest-vol/lowest-price/most illiquid quintile versus large caps, or exit lottery-stock shorts (idea 1) in January. Source: ER 18.4, 19.3 (liquidity premium concentrated in January, high-vol/high-skew stocks outperform in January; Doran-Jiang-Peterson). Evidence: qualitative. Fit: medium: only ~10 years of our share data (2015+) means few independent January observations: severe power problem; use as a conditioning filter of idea 1, not a standalone test. Differs: seasonal, but mechanism is risk appetite and year-end liquidity, not session timing.

6. **Variance-risk-premium timing of an equity-index long (CFD or futures)** - Signal: implied vol minus subsequent/realized vol (VIX minus past 21-day realized). Go long index when the gap is high (author: gap predicts next-quarter equity return, R2 15% in Bollerslev-Zhou); otherwise flat. Source: ER 19.3. Fit: we have Cboe VIX futures plus VIX data and index CFD prices; daily long-only timing, no swap if futures. Monthly-quarterly horizon with few independent observations (power problem). Differs: a volatility-state timer, not a price pattern. Likely falsified by costs/power; cheap to test since data exist.

7. **Average stock correlation as market-timing signal (US shares)** - Compute average pairwise correlation (or the market variance split into average variance and average correlation) from the 23,700-share panel, using a 1-3 month window; long the market (SPY-like basket or index CFD) when average correlation is high, flat otherwise. Source: ER 19.3 (Pollet-Wilson: average correlation predicts next-quarter market return positively; average variance does not). Evidence: significant in the book's long sample. Fit: good data (daily US shares), but very few independent quarterly observations in 2015+; treat as a research probe with a power check. Differs: panel-derived state variable.

8. **Weekly/monthly crowding and de-leveraging filter for our crypto and cross-sectional books** - Use realized rise in cross-strategy correlation, a spike in funding or taker flow imbalance, or sharp VIX rise as a risk-off trigger that scales down a long-short sort (not a stand-alone alpha). Source: ER 20.2, 18.3 (momentum and liquidity-risk strategies lose when funding tightens; crowded positions unwind together; short-term momentum in strategy returns with +0.20 monthly autocorrelation). Evidence: qualitative. Fit: applicable to Strategy 20 and any new sort; testable as strategy-return autocorrelation and drawdown conditional on funding/VIX. Differs: portfolio-level risk control, not a signal; supports our "shrunk forecast" method.

9. **Strategy-level momentum (time series of our own sort returns)** - Scale a long-short sort up if its own last month/quarter return was positive and down otherwise, since monthly autocorrelation across strategies averaged +0.20 (ER 20.2); check that it does not just add costs. Fit: good, since it only needs the strategy return stream; the autocorrelation can be tested directly with proper standard errors on Strategy 20 and the month-end Treasury sleeve. Differs: meta-level.

10. **Yield-curve slope as slow regime filter for the Treasury month-end extension / duration** - Condition the month-end duration trade on curve slope or real yield level (value/carry indicator, ER 21.1). The book suggests higher carry (steeper curve) gives higher expected bond return over long horizons but nothing short-term. Fit: FRED yields exist, but the conditioning will have very few independent observations; low prior, only a check for regime dependence of the already-passed stream.

### Warnings / pitfalls
- Peso problem: asymmetric-payoff strategies (vol selling, carry, correlation selling, illiquidity harvesting, betting against beta) show high Sharpe until the disaster; the disaster can be more than a decade apart; the sample may never contain it. Our 2015+ sample (incl. 2020) is short for these. (ER 19.1, 20.2)
- Premia decay after discovery and crowding: illiquidity premium and liquidity-provision profit declined; success attracts inflows that erode ex ante Sharpe while realized results stay good; then liquidation hits (Aug 2007 quant meltdown). Alpha morphs into beta. (ER 18.4, 20.2)
- Many cross-sectional anomalies live in small, illiquid, low-priced, hard-to-short stocks and weaken or reverse with value-weighting, size controls, large-cap-only samples, or in the 2000s. Use realistic price/volume floors and borrow costs. (ER 19.3)
- Research-design sensitivity: window length and return frequency flip the sign of the vol-return relation (1 month daily negative, 3 years monthly positive). Pre-register one definition. (ER 19.3)
- Contemporaneous factor correlations are not predictive; do not read Table 16.1 style results as signals. Aggregate earnings/growth news is forward-looking and its contemporaneous relation to returns is negative; the sign of growth-news reaction depends on the cycle stage. (ER 16.4, 16.6)
- Do not confuse market cap or GDP growth with investor returns (dilution; ER 16.3). Valuation ratios and carry predict only over long horizons; short-term use is noisy. (ER 21)
- Liquidity-based Sharpe ratios are overstated by smoothing and stale prices; BEI/TIPS-type spreads reflect liquidity premia as much as the macro quantity named. (ER 17.3, 18 note 1)
- Short-term vol-return relations are contaminated by bid-ask bounce and by leverage/volatility-feedback effects. (ER 19.3)
- Risk-control spirals: stop-loss/VaR rules sell into weakness, so signals driven by the same flows are crowded when markets are stressed. (ER 20.1)
- Time-varying premia: tail-risk and liquidity premia are largest right after the loss and smallest after a long calm; timing is hard, early contrarian buyers bleed (vol buyers 2005-07). (ER 18.4, 19.6)

# Part 5: ch.22-29: carry, surveys, tactical forecasting, seasonals, cycles, secular trends, risk and horizon, takeaways


Citation style: printed page numbers do not appear in the text file, so cites are chapter.section (ER 25.2 etc.).
Lines ~25029-28943 are only the bibliography (nothing to extract). Appendix A (world wealth) and B (data sources) skimmed.

### Overview
- This part is the "so what" half of the book: how to read yield spreads (carry), surveys, tactical forecasting models,
  seasonals, business-cycle and secular variation, and finally portfolio-level ways to enhance returns (risk, horizon, skill, costs).
- Stance: a practitioner and risk-premium believer. Carry, value, momentum/trend and illiquidity are the sources he trusts;
  expectations hypotheses (UIP, PEH) fail empirically. He repeatedly warns about data mining, crowding and costs.
- It is almost all low-frequency (monthly, multi-year) and long-horizon. Very little is directly testable on M1 data. The valuable
  parts for us are (a) the carry/roll logic, which maps to futures curves and crypto funding, (b) the seasonal chapter with its honest
  verdict (weak, mostly eaten by costs), (c) the honesty tools (fundamental law, breadth, variance drain, rebalancing return,
  timing of losses) and (d) the cost chapter (signal speed vs turnover, avoid trading with the index crowd).
- Not much hard performance data is given in text; most numbers sit in figures that did not extract. Where numbers exist they are listed below.

### Chapter notes

### Ch 22 - Yield spreads: expected returns or market expectations? (ER 22.1-22.4)
- Identity: return = carry + capital gains. An initial carry advantage is either offset by later price moves (expectations
  hypothesis: UIP for FX, pure expectations hypothesis PEH for bonds) or it is simply earned (risk-premium / random-walk view).
  Forward rates are break-even rates, NOT the market's forecasts unless risk premia are zero.
- "Complementary regression" method (Fama-Bliss): regress future price change on the forward-implied change AND future excess return
  on the carry; the two slopes sum to 1. Slope on the excess-return regression is the "persistence factor" PF (1 = carry fully earned).
- FX, monthly 1978-2009: future spot change regressed on forward premium gives negative slopes (EUR -0.7, GBP -2.2, CHF -1.2,
  JPY -2.6, CAD -0.8), so excess-return slopes are 1.7 / 3.2 / 2.2 / 3.6 / 1.8. High-yield currencies tended to appreciate further.
  The real horse race is random walk (PF=1) vs an even more pro-carry story; UIP (PF=0) is rejected.
- US Treasuries, monthly 1972-2009: PF for 2y 1.2, 5y 1.6, 10y 2.5 (yield-change slopes -0.2, -0.6, -1.5). Correlation of curve steepness
  with next-quarter 10y excess bond return +0.21 (with yield change -0.13). PF has drifted down over time but stayed positive, around 1.
  Curve steepness has become a weaker duration-timing signal, yet cross-country carry (hedged G10 bonds, steep vs flat curve) still earned decent SR.
- Credit: correlation of spread with subsequent excess return over Treasuries +0.12 monthly, +0.48 annual (1973-2009), positive in rolling 10y windows.
  Average default losses are far below average spread, so part of the spread is a real premium.
- Equities: dividend yield predicts returns, not dividend growth (Cochrane). Value stocks outperform; growth gap is smaller than valuation gap implies.
- Commodities: backwardation predicts higher returns; long-run commodity futures return is largely explained by roll return. WTI since 1987:
  spot-change slope on roll 0.5 and excess-return slope on roll 0.5, i.e. split half and half (steep backwardation predicts some spot fall AND some excess return).
  Seasonal agricultural backwardation predicts spot changes even more.
- Volatility: inverted vol term structure predicts falling vol AND high reward for vol selling; variance-swap slopes below 1 (Carr-Wu), same split in EUR/USD implied vol.
- Rolling yield / rolldown: carry should include the pull-to-par and roll-down along the curve (e.g. 20bp x duration 4 = 0.8% in an unchanged curve);
  the same idea works for credit spread curves, commodity futures roll-up and option time decay.
- Conclusion: carry predicts near-term returns better than it predicts offsetting price moves, in every asset class studied. But part of it is
  biased expectations, not only risk premium. Pitfalls: crowded carry trades de-lever together; hyperinflation drift; structured products with fake yield.

### Ch 23 - Survey-based subjective expected returns (ER 23)
- Surveys = real-time ex ante views. Problems: representativeness, staleness (forecast date vs survey date), mean vs median vs mode, gaming.
- Retail equity-return forecasts are procyclical and extrapolative (high after bull runs), the opposite of valuation-based expectations,
  which are countercyclical. Professionals/CFOs sit closer to valuation measures.
- Survey-based bond risk premium (10y yield minus consensus forecast of short rates): trended up in 1970s, peaked 1979-85, fell for 20 years.
- Philly Fed survey: bond premium over bills fell from 2.5% to 0.5% by 2007; equity premium around 2%.
- Recent studies: much classic return predictability is not related to survey-based ex ante premia but to systematic forecasting errors, or just overfitting by the econometrician.
- Relevance for us: low (no survey data). Possible idea: contrarian use of sentiment extremes, but no data feed.

### Ch 24 - Tactical return forecasting models (ER 24.1-24.6)
- Two classes: single-asset timing and cross-sectional selection. Indicators: value, carry, momentum, plus macro, supply/demand, sentiment, liquidity.
- Bond timing example 1978-2009: average of three binary signals (equities lost money in last 6 months, bond momentum positive, bond carry positive),
  1/-1 positions, SR 0.66, hit rate 60% of months.
- Regression timing: regress next-month excess return on z-scored indicators; coefficient = partial correlation; position = fitted value; constrain the intercept
  (do not let a historical bull-market mean become the neutral forecast); impose sign constraints from economic priors.
- Simple (sum of binary signs) often matches complex models out of sample and is more robust.
- Cross-section: single sort, composite average-rank across criteria (e.g. G10 FX on carry+momentum+value; "works surprisingly well"), or cross-sectional regressions
  (Fama-MacBeth style, slope = factor-mimicking portfolio return).
- Black-Litterman suggested for combining model views with uncertainty.
- Cost logic: high-turnover/fast signals need very high gross SR or very low costs; slow signals tolerate higher costs.
- Taxonomy (Table 24.2): time-series vs cross-sectional x price patterns / seasonals / other. Short-term and long-term reversal, intermediate momentum;
  the equity momentum/reversal timing profile does not generalize to other asset classes.
- Convergent (carry, value, mean-reversion, vol selling) vs divergent (trend, momentum, long vol) strategies.
- Enhancements: style timing (carry fails in high vol / tight liquidity; many styles show mild short-run momentum and long-run reversal in their own returns), contextual models
  (trend works better in poorly anchored macro assets than anchored micro assets).
- Pitfalls: in-sample regressions exaggerate; rolling out-of-sample still has hindsight in indicator choice; persistent predictors and long-horizon regressions give spurious results;
  crowding (1998, Aug 2007, 2008: all systematic strategies de-leveraged together); regularities decay fast once public.

### Ch 25 - Seasonal regularities (ER 25.1-25.3)
- Headline: seasonals are weak, possibly spurious, vulnerable to competition, and mostly smaller than trading costs. Practical use = only to delay or advance trades planned for other reasons.
- Equities historically high in Dec-Jan, negative Sep-Oct; government bonds weak early in year, strong in autumn.
- January effect: appears in carry (credit carry, FX carry, long USD), small caps, value, high-vol stocks, high-yield credit, reversal strategies. Momentum/trend do the opposite
  (good in December, reverse in January). Bond term premium is earned only outside January. High-vol stocks only outperform in January. Most of the effect is in the first few trading days of the year.
  The equity and value premia in January flipped sign (below average) over the last 20 years of the sample, perhaps because the effect became known; it also started to work in late December.
- Explanations: tax-loss selling, window dressing (buy government debt and winners in Nov-Dec), seasonally high risk appetite / gambling preference at the start of the year (lottery-type
  stocks do best in January; Chinese lottery stocks around Chinese New Year; OTM calls richer in January), bonus and drawdown-limit resets, and liquidity (high-liquidity-beta state in 59% of Januaries vs 14% of other months).
  Low liquidity plus high costs can make quoted-price moves at year end look like returns that nobody could trade.
- January barometer: January return of risky assets predicts the next 11 months (consistent across risky assets; worked in 2008, failed in 2009).
- Halloween effect: Nov-Apr strong, May-Oct weak, echoed in small caps, high-vol, credit, carry.
- Other seasonals: within-day (volatility U-shaped; major currencies tend to weaken during their own time zone's trading hours - diversification outflow flows); day-of-week (Monday effect
  disappeared after discovery in 1970s); turn of month (McConnell-Xu: all US equity excess return 1926-2005 earned in a 4-day window = last business day plus first 3 business days;
  Grimbacher et al.: 5 business days from last day of month beat other days by 17-37 percentage points annualized in every decade 1960s-2000s, the most consistent seasonal; the effect has moved earlier);
  holiday effect (day before major holidays, also non-US holidays like Chinese New Year, Golden Week); lunar cycle (new moon fortnight better than full moon - he is skeptical);
  announcement days (higher average returns on macro/earnings days, and run-up momentum into events: bonds before payrolls, oil before OPEC meetings, agriculture before supply/demand reports);
  12-month periodicity (stocks outperform/underperform in the same calendar months each year); commodity supply-demand seasonals (agricultural prices higher before harvest, heating/cooling energy demand) -
  mostly in the futures curve already, but only partly, so seasonal excess returns may remain; presidential cycle (partly broken down).

### Ch 26 - Cyclical variation in asset returns (ER 26.1-26.2)
- 1927-2009 NBER phases: economy expanded in 80% of months. Equity realized excess returns are high around troughs and low around peaks (countercyclical risk premium); bond premium low near peaks;
  size premium behaves like equities; value has little cyclicality (pre-war-driven); momentum is a diversifier near peaks and mid-recession, but hurt at troughs when defensive-to-cyclical handover happens.
- Ex ante indicators (dividend yield, credit spread, curve steepness) fall in expansions and rise in contractions; curve is flattest at troughs and steepest near peaks (best timing match).
- 1960-2009 growth/inflation/volatility quadrants (quarterly): equities best in disinflation and stable (low vol) regimes, worst in inflationary booms (monetary tightening: +32bp short-rate moves);
  bonds best in disinflationary or stable stagnation, lose when inflation rises; commodities and housing best in inflationary boom (growth dimension critical); small caps do best in inflationary/volatile stagnation;
  value shines in booms; equity momentum and trend following are profitable in all 8 regimes, best in inflationary/volatile booms; FX carry and credit carry profitable in all 8 regimes, better in disinflation.
- Caveats: judgmental regime proxies, regimes only identified in hindsight, contemporaneous (not predictive) relations, relations drift (bond/vol link flipped after 1980s).

### Ch 27 - Secular trends and the next 20 years (ER 27)
- 1988-2007 was exceptionally benign (disinflation, falling macro vol, valuation expansion, stock-bond correlation moved from +0.4 to -0.1, high real returns, low vol) vs 1968-1987.
- Reversing trends listed: free-market capitalism, disinflation, rising leverage, financialization, asset richening. Sustainable: technology, rise of emerging markets, aging, globalization, environment.
- Warning for backtests: secular trends are landmines for mean-reversion or fair-value models built on backward-looking history. Mostly discretionary and speculative; low value for us.
- Stock-bond correlation regime and the level of yields (starting yields low) affect risk parity and bond safe-haven assumptions.

### Ch 28 - Enhancing returns: risks, horizon, skill, costs (ER 28.1-28.5)
- 28.1.4 / 28.5 COSTS (important for us): S&P 500 loses ~20-30bp per year from market impact of index additions/deletions; GSCI owners lose from predictable monthly rolls. Do not trade at month ends or in
  popular index products when the crowd trades. Persistent slow signals (value, carry) need less turnover than fast decaying ones (momentum/reversal), so higher costs shift weight to slow signals.
  Israelov-Katz: even long-horizon investors benefit from fast signals by delaying or skipping trade execution when the fast signal says wait. Reversal strategies supply liquidity; their performance co-moves
  with VIX (liquidity proxy). Demanding liquidity is most expensive in high vol; supplying liquidity is better rewarded in turbulence. Stale limit orders are a big source of retail losses.
- 28.2.1 Risk parity: 60/40 nominal has >95% of risk from equities. Equal-vol stock/bond (1970-2009) SR 0.40 vs 0.38 for nominal 60/40, correlation to equities 0.76 vs 0.96; gains rise with lower stock-bond correlation.
  Leverage aversion makes high-vol assets overpriced within asset classes: high-vol and highly levered stocks earn low returns, duration extension pays better at the front end, CCC bonds the worst rating bucket,
  Treasury-to-credit switch pays at short maturities. Lever low-vol assets instead.
- 28.2.2 Rebalancing/diversification return: GM ~ AM - variance/2 (equity 20% vol -> ~2% drain; US large caps 1926-2006 AM 12.3%, GM 10.4%; bonds with 6-7% vol -> ~0.2%).
  Diversification return DR rises with number of assets, average variance, and falls with average correlation; it requires constant-weight rebalancing (covariance drag otherwise).
  Erb-Harvey example: 50/50 heating oil and stocks annually rebalanced over a decade had GM excess return 11.0% vs 8.2% (oil, AM near 18%) and 6.8% (stocks, AM near 9%), DR ~3.5%.
  Rebalancing is worse than buy-and-hold only when expected return gaps are very wide (e.g. T-bills vs high-return assets). With short-term momentum, too-frequent rebalancing hurts; with costs, longer intervals win.
  Volatility targeting: constant vol targeting stabilizes risk and often improves long-run return vs constant nominal size, because near-term higher vol does not bring higher near-term expected return.
- 28.2.3 Beyond the Sharpe ratio: timing of losses (carry lost money in 11 of the 15 worst months for global equities 1985-2009; trend made money in 13 of 15), return asymmetry
  (trend has positive skew, small max drawdown; carry = selling lottery tickets with toxic timing), liquidity (illiquid assets have smoothed, overstated SR), unquantifiable tail risks (Madoff).
  Both carry and trend proxies had paper SRs near 1, costs but not fees subtracted; net-of-fee CTA indices SR 0.2-0.5.
- 28.2.4 Smart portfolio construction: equal-vol across return sources unless SR or diversification justify deviation. Fundamental law: IR = IC x sqrt(breadth). Updating a view weekly instead of annually
  boosts IR ~7x (sqrt 52) at the same skill, but only if forecasts really stay accurate and costs allow. Breadth assumes independent bets; correlated bets count less. Super-diversifiers: value vs momentum, carry vs trend.
  Stop-loss and risk controls reduce expected return unless there is timing skill. Robust simple measures beat complex ones in a world of outliers and estimation error.
- 28.3 Horizon: compound growth, rule of 72, time diversification debate (volatility of average return falls, volatility of cumulative loss rises; parameter uncertainty adds long-horizon risk - Pastor-Stambaugh).
  Dollar cost averaging is suboptimal unless mean reversion.
- 28.4 Skill: active management zero-sum before costs, negative-sum after; Litterman "active risk puzzle"; most mutual funds lose after fees (French 2008: ~70bp/yr aggregate overspending);
  dumb-money gap: dollar-weighted returns trail time-weighted by ~1.5% (mutual funds) and 3-7% (hedge funds). Berk-Green: skilled managers raise AUM until rents vanish. Skill needs breadth; systematic
  investors exploit breadth better than discretionary. Liquid markets let you tell luck from skill quicker.
- Box 28.4 Taxes: tax-loss selling feeds turn-of-year effect.

### Ch 29 - Takeaways for long-horizon investors (ER 29.1-29.5)
- 10 return sources scorecard (does it pay in the long run?): (1) high vol/beta - NO within asset classes (lottery preference, leverage constraints), yes across classes;
  (2) illiquidity - yes; (3) fast growth - no; (4) cheap assets (value) - yes; (5) positive carry - yes, esp. cross-country, with poor timing of losses;
  (6) recent distress - no in equities (distressed keep underperforming for months), but fallen-angel bonds earn high returns after forced institutional selling;
  (7) recent success (momentum 6-12 month) - yes, multi-year chasing is reversal; (8) leverage - yes but risky; (9) diversification - yes if monetized by leverage; (10) timing - yes in moderation.
- Mechanisms named: lottery preferences, leverage constraints (willing to overpay for embedded leverage), forced selling by institutions (fallen angels), career risk, window dressing, crowding.
- Debates: alpha-beta barbell (most risk cheap, small costly active sleeve); insurance/lottery SELLING beats lottery buying long run (short vol, carry), pair with trend/momentum as the tail diversifier;
  moderate market, factor and style timing endorsed with humility; style diversification (value vs momentum, carry vs trend) beats asset-class diversification: Box 29.2 composite of 4 styles (equity value,
  FX carry, commodity trend, vol selling) 1990-2009 had correlation to global equities 0.27 and average pairwise correlation -0.05 vs 0.80 / 0.30 for 4 asset classes; SR 1.2 vs average constituent 0.6.
  He warns style paper performance is more overstated (overfitting, ignored costs) than asset-class performance.
- Large players should avoid trading synchronously with other large players (customized benchmarks).
- Appendix B.2 note: "no trading costs have been subtracted from any of the strategy style returns" - so his style Sharpes (carry, trend, value, vol-selling) are GROSS.
  Carry strategy base case: each week buy top-3 and sell bottom-3 G10 currencies by yield. Trend style: long/short if price above/below 12-month moving average, applied weekly on commodities, equity index futures, bond futures, FX.

### Topic tags
- trend: trend-following style SR near 1 gross (simple 12-month MA rule, weekly, across 4 asset classes), positive skew, small drawdown, made money in 13 of 15 worst equity months and in all 8 growth/inflation/vol regimes; net-of-fee CTA indices SR 0.2-0.5 (28.2.3, App B.2). Works better in poorly anchored macro assets. Reverses in January (25.2).
- breakout: not covered.
- mean-reversion: short-term reversal supplies liquidity, comoves with VIX; January reversal premium (25.2, 28.5); long-term reversal beyond 12 months; contrarian valuation timing for long horizons (29.3.5).
- momentum/oscillators: best information in 6-12 month history (29.2 item 7); momentum loses in January, wins in December; momentum good diversifier in mid-recession, bad at cycle troughs (26.1); chasing multi-year returns = reversal.
- patterns: not covered (price patterns appear only as the taxonomy: momentum/reversal).
- intraday/sessions: within-day return patterns are weak; vol higher at open and close and at announcements; FX majors weaken in own-time-zone hours (Breedon-Ranaldo 2008) (25.3). High-frequency strategies feasible only at the lowest costs and mostly act as liquidity suppliers (24.4).
- volatility: inverted vol term structure signals both falling vol and high vol-selling reward; vol selling is a premium with negative skew; vol-targeting stabilizes risk and often improves return; high-vol assets overpriced within asset class.
- seasonality/time: January effect (first days of year), January barometer, Halloween (Nov-Apr), turn-of-month (last day + first 3 days; the strongest and most consistent), pre-holiday, announcement-day premium and pre-announcement drift, commodity supply/demand seasonals only partly priced in futures, 12-month periodicity, presidential cycle (decayed). All weak and decaying; "costly to exploit".
- stops-and-exits: stop-loss limits lower expected return unless there is timing skill (28.2.4); drawdown control is the absolute-return managers' survival tool (29.3.7).
- position-sizing/risk: equal-vol allocation across return sources; vol targeting; risk parity; fundamental law (breadth); variance drain GM = AM - var/2; leverage only on low-vol liquid assets.
- testing-and-robustness/overfitting: in-sample regressions exaggerate; hindsight in indicator selection even in rolling OOS; persistent predictors and long-horizon regressions give spurious results; seasonals easy to data-mine "the one history we have"; simple equal-weighted binary signals competitive with regressions; paper style performance (no costs) overstated; ex-post alpha mixes luck and skill; judge ex ante decision quality.
- costs/execution: turnover vs signal decay; slow signals tolerate costs; index add/delete cost ~20-30bp/yr; do not trade with the crowd (month ends); liquidity-demanding costs most in high vol; seasonals mostly eaten by costs; use fast signals only to time execution of trades you plan anyway.
- psychology/discipline: retail extrapolation of returns, lottery preference, career risk of being "right but early", comfort-seeking reduces returns (Box 29.1), tie yourself to the mast if governance is procyclical.
- portfolio/diversification: style diversification beats asset-class diversification (value vs momentum, carry vs trend; Box 29.2); rebalancing return; correlations rise in crises, carry correlates with equity losses; trend/gov bonds were the safe havens in 2008.

### Testable ideas
All ideas below are low-frequency; the book gives very few hard numbers. Most promising marked with a star.

- **Carry/roll as a cross-sectional sort on futures curves (EIA energy contracts 1-4, VIX futures, Treasury continuous)** - each week/month rank markets by annualized roll yield (front-to-second contract log ratio scaled by days), long the most backwardated, short the most contango, vol-scaled to equal risk, hold to next rebalance. Source: Ch 22.3 commodities, 29.2 item 5. Evidence: backwardation predicts returns; WTI since 1987 PF=0.5 (half of the curve slope is earned as excess return, half is offset by spot fall). Fit: ok for EIA contracts 1-4 (WTI, Brent, gasoline, heating oil, natgas ~5 markets, small cross-section; futures cost model). Differs from spent GSCI roll test: that tested index-roll flow timing, this tests curve-slope carry as a forecast variable (and its conditional PF), including the state that a steep curve also predicts spot falls.
- ★ **Complementary-regression carry audit on crypto perp funding** - for each coin, regress next-week excess return on funding rate (annualized) AND next-week price change on funding; check whether the slope split is carry-earned (PF near or above 1) or offset (PF near 0). Trade only when the split supports it (e.g. funding sorted weekly long/short). Source: Ch 22.2-22.3 method; rule transfers directly from FX (forward premium = funding rate). Evidence: FX PFs 1.7-3.6, bonds 1.2-2.5; credit and commodities between. Fit: good - Binance perps prices, funding, taker flow are in our data, costs known; weekly horizon aligns with Strategy 20. Differs: not a price pattern; it is a payoff-identity test of whether paying side is compensated, and gives a falsifiable PF number before any trading. Also gives a shrinkage target (if PF<1 shrink carry forecast).
- ★ **Cross-asset sort on rolling yield for Treasury futures / FRED yields (curve carry timing)** - monthly: long 10y futures when curve slope (10y minus 2y or 3m) is above its trailing median, flat or short otherwise; or scale position by steepness z-score. Source: Ch 22.3 (PF=2.5 at 10y, steepness-return correlation +0.21), 24.2 (bond timing SR 0.66 with 3 binary signals: equity 6-month loss, bond momentum, carry). Fit: good - FRED yields and Yahoo 10y futures exist; one asset, so few independent bets (check power!). Differs from the passed month-end duration extension: this is a monthly slow carry timing, not a calendar flow; expect it to overlap in the long-Treasury exposure, so test as incremental to month-end and check correlation. Honest power note: at 0.66 SR with ~15 years of monthly data, t is only about 2.5.
- **Equal-weighted 3-signal binary composite for duration timing (equity 6-month loss, bond momentum, bond carry)** - monthly, long/short 10y futures at +1/-1 (or 1/0). Source: Ch 24.2, Fig 24.1, SR 0.66, hit rate 60%, 1978-2009. Fit: data ok; sample for futures from Yahoo continuous is shorter; costs low (one liquid contract). Differs from our failed trend families because the signal blends cross-asset equity weakness (flight to quality) with carry. Possibly the same as month-end test for duration; check overlap.
- **January/turn-of-year effect on our US share universe (daily, Alpaca)** - long the first ~5 trading days of the year in a basket of high-volatility / lottery-type (price low, vol high, skew high) US shares vs low-vol shares; hold 5 days, equal weight, short low-vol or index. Source: Ch 25.2 (Doran-Jiang-Peterson: lottery stocks outperform only in January; high-vol minus low-vol premium earned only in January; most gain in first days of the year). Evidence: figures only; effect flipped sign for equity/value in last 20 years of his sample, so we have only ~9 Januaries since 2015 on shares - massively underpowered (one trial per year). Fit: poor on power, good on cost (real shares, long-short but short borrow costs); mark as unproven-positive at best. Differs: calendar rule on cross-section, not index flow.
- **Turn-of-month equity drift (last day + first 3 business days) on US index CFDs / shares, as a hold-or-skip filter** - hold index long only from last trading day of month through third trading day of next; else flat. Source: Ch 25.3 (McConnell-Xu 4-day window explains all excess return 1926-2005; Grimbacher 5-day window 17-37 pp annualized better in each decade). Evidence stronger than most seasonals. Fit: our CFD swap/overnight financing is paid only on the nights held (about 4-5 nights per month, the effect is that the rest of month is not held, so financing is low); spread cost per round-trip ~ once a month. BUT very close to the already spent "month-end index flow" test - treat as a re-check on different instruments (US shares/ETF basket, daily) and not as new; most likely already covered. Mark as caution/duplicate.
- ★ **Announcement-day premium and pre-announcement drift (macro releases)** - go long index/duration the day before (or morning of) FOMC/CPI/NFP announcements, exit at close of announcement day; or stay in bonds before payroll. Source: Ch 25.3 (average returns higher on major announcement days; momentum into announcement dates: bonds before payroll, stocks before earnings, oil before OPEC, agri before WASDE). Fit: we have M1 data on indices, gold, oil; need an event calendar (FOMC dates public, EIA inventory dates). Costs: one round trip per event on liquid CFDs - moderate; for the oil CFD the weekly EIA inventory day gives 52 events/year, enough power. Differs from failed intraday session rules: it is an event-conditioned holding (compensation for uncertainty / forced pre-event positioning), not a session or price pattern. Evidence from the book: qualitative (no numbers in text).
- **Commodity seasonal at partly priced curves (EIA nat gas, heating oil, gasoline)** - hold the contract with positive seasonal expected return (nat gas before winter withdrawal season, gasoline before driving season, heating oil autumn) as excess return over the curve, rolled at fixed days; test with contract-1 vs contract-2 return, i.e. seasonal excess return on futures, not spot. Source: Ch 25.3 supply-demand seasonals "only partly built into futures prices". Fit: EIA futures contracts 1-4 give true futures returns; ~20 years per seasonal gives 20 observations per season: tiny sample, compare to a cross-sectional placebo (random start months) to calibrate the multiple-testing ledger. Differs: not the GSCI roll test (that was a flow window); this is a fundamental seasonal expected-return premium.
- **Fallen-angel / forced-selling rebound analogue for US shares: index deletions and downgrades** - after a large share is removed from an index or hits a rule-based forced selling event (S&P deletion, ETF reconstitution, dividend/quality threshold), buy after the forced-flow window and hold weeks. Source: Ch 29.2 item 6 (fallen angels earn high returns after forced institutional selling), Ch 28.1.4 (index add/delete price pressure ~20-30bp per year of drag for indexers). Fit: needs index membership data, which we lack except through Alpaca price history (could proxy by sudden relative drop plus volume); mark as needing data. Differs: a must-trade counterparty (index funds) idea rather than a price pattern, aligned with the project focus.
- **Volatility-managed overlays on our existing passed streams (Strategy 20, month-end duration)** - scale exposure each period to target constant volatility (trailing 20-60 day realized vol). Source: Ch 28.2.2 ("targeting constant volatility often improves long-run returns"; near-term higher vol does not bring higher near-term return). Fit: fully testable on R/daily stream, no new costs except size changes. Check on the existing passed trade lists; but careful, it is a post-hoc tweak, so it needs its own pre-registered gate; test increment in SR and drawdown R. Differs: a risk-layer, not an entry rule.
- **Style-timing: switch off carry-type streams when vol/liquidity stress rises** - for FX carry-like or funding-carry streams, scale down when VIX futures backwardation, crypto realized vol or funding dispersion spikes. Source: Ch 24.5 (carry underperforms amid heightened vol, tightening liquidity), 28.2.3 (carry lost in 11 of 15 worst equity months). Fit: VIX futures and crypto prices on hand; test as a conditional filter on Strategy 20 (already passed, so the filter must be a separate pre-registered variant and risks being a second look at the same data). Differs: filter on an existing premium, not a new entry.
- ★ **Rebalancing/diversification return across our passed streams and across crypto perps** - quantify that equal-risk-weight rebalanced combination of low-correlated streams beats the best single stream's GM, and that unrebalanced mixes lose it. Source: Ch 28.2.2 (DR ~ half the average variance times diversification; Erb-Harvey 3.5%). Fit: it is an analysis, not a signal; cheap and honest. Use to size the portfolio of Strategy 20 + month-end duration + any carry stream. Differs: portfolio construction, helps the "balances itself across regimes" goal.
- **Composite-rank multi-signal for crypto perps or US shares (rank-average of carry, momentum, value-like)** - each week rank assets on several signals (funding/carry, 12-1 style momentum, valuation or taker-flow), average ranks, long top third short bottom third. Source: Ch 24.2 (composite-rank "works surprisingly well", Ilmanen-Sayood). Fit: good on crypto perp universe and US shares daily; check turnover: a weekly sort of ~100 coins with ~50% turnover pays fees (maker/taker); shares need borrow costs. Differs: multi-signal averaging reduces the one-signal multiple-testing exposure (fewer free parameters than tuning one signal), but it is still a combination of tested ingredients, so count each in the ledger.

### Warnings / pitfalls
- Seasonals: easily data-mined on a single history; decay once published (January effect moved into late December, value/equity January premia flipped sign in last 20 years of his sample; Monday effect vanished; turn-of-month moved earlier); most are smaller than costs (ER 25.1-25.3).
- Strategy style returns in the book (carry, trend, value, vol-selling) are before any trading cost (App B.2); net CTA index SR only 0.2-0.5 versus ~1 for his gross trend proxy. Treat gross SRs as ceilings.
- Carry is negatively skewed and crashes with equity and liquidity: lost in 11 of 15 worst equity months; crowded carry trades de-lever together (1998, 2007-08). Selling lottery tickets: pays long run but needs a loss budget.
- Regime tables (growth/inflation/vol quadrants) use judgmental proxies and are contemporaneous; regimes are not known in real time; relations flip over time (bond/vol link after 1980s).
- In-sample regression fit and long-horizon regressions on persistent predictors give spurious predictability; even rolling OOS has hindsight in indicator choice. Survey-implied predictability may just be systematic forecasting error.
- Breadth in the fundamental law assumes independent bets; many strategy trades use the same information and are positively correlated, so effective breadth is smaller. Weekly updating multiplies IR by ~7 only if skill per forecast does not decay and costs do not eat it.
- Stop-loss rules and drawdown controls lower expected return unless there is timing skill.
- Variance drain: use geometric mean, not arithmetic, for long-horizon return claims (AM-GM ~ var/2); unbiased future wealth estimate moves toward GM with horizon and estimation error.
- Do not trade in sync with the crowd (month-end, index events) if you are the one paying; the same crowd flows are the edge for the side that supplies liquidity at the right price (relevant to our month-end duration finding: capacity and decay risk once known).
- Complexity does not reliably help out of sample; simple equal-weight binary signals are often as good and more robust.
- Style diversification benefits look larger on paper than in practice because style performance is more prone to overfitting and ignored costs than asset-class returns (Box 29.2).

