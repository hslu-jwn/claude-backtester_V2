> Reading notes, own words, made 2026-10-16 from the PDF in `00_Literature/Trading`. Part of the knowledge base: see [../README.md](../README.md). Synthesis across books lives in `../topics/`, strategy ideas in `../ideas.md`.

> Cited as RC with the print page.

# Notes: Robert Carver, *Systematic Trading* (Harriman House 2015)

Read: whole book (front matter, ch 1-12, ch 13 rules and process, ch 14 setup, ch 15 setup and numbers, epilogue, appendices B, C, D). Skimmed: diary tables in ch 13-15, glossary, appendix A (resources). Page numbers are the print-edition numbers the book itself cites (the text file has no page headers); where I give "~" the page is inferred from cross-references.

## Overview

Carver (ex-AHL, trades 40+ futures himself) gives a modular framework for turning any price-based opinion into a position:
(1) scaled forecast per rule variation (target average absolute value 10, cap 20), (2) weighted average with forecast weights,
(3) times a forecast diversification multiplier (FDM) back to average abs 10 and cap again at 20, (4) volatility targeting of the
account (percentage vol target from a pessimistic Sharpe, half Kelly), (5) position = forecast x volatility scalar / 10 per instrument,
(6) instrument weights and an instrument diversification multiplier (IDM), (7) position inertia (10%), (8) speed limit from costs.
Stance: humble, pessimistic, simple. Fit almost nothing; do not select rules by performance; use few ideas, several speeds each,
diversify over instruments more than over rules. Realistic Sharpe is low: 0.3-0.4 per instrument and rule set, about 1.0 as an
absolute ceiling for a very diversified system. Costs and over-betting are the main killers, not lack of clever rules.
Everything is volatility-standardised so the same rule runs on every instrument and results can be pooled.

## Chapter notes

### Ch 1 - The Flawed Human Brain (pp. 17-35)
- Disposition effect (prospect theory): people take small profits and hold losers. His "A and B" test (App B): early loss taker (profit target A=20, stop B=5, in daily-sigma units, always long or short, reverse on hit) beat early profit taker (A=5, B=20) on 27 of 31 futures. Claimed reason for trend following edge: other people's bias.
- Meddling (overriding the system) is the biggest cause of bad results; commitment mechanisms: objective rules, automation, fixed risk.
- Three design sins: over-fitting, overtrading, over-betting (leverage). Example: 10x leverage means about 200% annual sigma, which is "nuts".
- Normal-distribution warning: Dow fell more than 4 sigma about 30 times in 1914-2014 (normal says once a century). Predictable risk = recent daily sigma; unpredictable risk is the rest.
- Annualise sigma with sqrt(256)=16; average returns by x256.

### Ch 2 - Systematic Trading Rules (pp. 37-56)
- Ideas first (hypothesis then test) vs data first (mine patterns). He prefers ideas first: simpler, explainable, less fitting. Warns ideas first still suffers implicit over-fitting because we only test ideas we already know worked. Loss-making systematic trading he saw was usually haphazard data mining.
- Why rules fail live: never worked (over-fit, look-ahead data, survivorship, costs underestimated, too short history, peso problem for negative skew), or the world changed (crowded relative-value trades).
- Why rules earn money: risk premia (persistent, time-varying), skew premium (negative skew pays), leverage constraints, liquidity, forced traders (carry), barriers to entry, behavioural bias, self-fulfilling levels (Fibonacci etc. may work but no guarantee), pure skill (not systematisable).
- Skew table (p. ~39): same Sharpe 1.0 negative-skew vs positive-skew asset: hit rate 59% vs 46%; worst daily loss -22% vs -10%. Steady wins and high hit rate means probably hidden negative skew. Trend following = positive skew; FX carry, relative value, option selling, market making = negative skew. Compare rules by Sharpe only within the same skew.
- Law of active management: Sharpe grows with sqrt(number of independent bets). 1 bet/yr SR 0.15; 4 bets 0.30; daily (256) 2.4. Caveats: skill differs by horizon, costs ignored, rules have a "sweet spot" holding period. Sharpe falls for holding periods beyond a few months. Four uncorrelated assets double the Sharpe; diversifying across half a dozen asset classes gives 2-3x single-asset Sharpe.
- Achievable Sharpe (p. 52): single stock long-only 0.15 (excess return 3%/yr, sigma 20%); 20+ stocks one country or an index 0.20; global equities 0.25; multi asset class static 0.40 (max for static). Dynamic rules, diversified set, single instrument: about 0.40; across asset classes about double. Semi-discretionary single instrument 0.25, portfolio at most 0.50. Hedge-fund (CTA) data: none sustained SR above 1.0 for more than a few years. His own 40+ instrument system back-tests at about 1.0.
- Two shortcuts to fake high Sharpe: negative skew (his example 4.6 SR for 20 years then -100%; LTCM also about 4.6) and trading faster.
- Table 2 (p. ~54): if monthly-holding SR is 0.40, theory says SR 0.83 weekly, 1.8 daily, 2.6 half-day, 5.2 hourly. After costs: futures 0.37 / 0.71 / 1.2 / 1.4 / 0.28; retail spread bet 0.28 / 0.27 / -0.75 / -2.5 / -16.4. Message: speed pays only if costs are tiny; with retail-type costs anything faster than weekly is hopeless.
- Skew-aware sanity: one third of his own system is negative skew (carry); wants a mix of styles.

### Ch 3 - Fitting (pp. 57-77)
- "50 model kid" story: hundreds of tested rules, some always look good. Ideas-first fitting = pick rules from a list then calibrate parameters; the main danger is too many variations.
- Time machine problem: in-sample fit and test is dishonest. Alternatives: half split (honest but wasteful), expanding window (anchored, his preferred), rolling window (needs enough years). Use only past data at each step.
- Experiment on gold futures, 90 variations of the early loss taker, yearly refit by trailing 12-month Sharpe: best-of-last-year gave SR 0.07; random variation each year gave 0.20; equal blend of all 90 gave 0.33. So equal weighting of all variations beat picking the best.
- Multiple testing (Table 3, p. ~68): pool of zero-skill rules, one year of data, number accepted on average. Threshold SR 0.5: 1 rule tested accepts <1; 5 rules 1.4; 10 rules 3; 50 rules 16; 100 rules 30. Threshold 1.0: <1 / <1 / 1.5 / 8 / 16. Threshold 2.0: <1 / <1 / <1 / 1.2 / 2.3.
- Table 4 (p. ~69): Sharpe cutoff needed for a 5% chance of accepting at least one bad rule. Rules tested vs years of data (1 / 5 / 10 / 30 years): 1 rule 1.5/0.7/0.5/0.4; 5 rules 2.3/1.1/0.8/0.5; 10 rules 2.8/1.2/0.8/0.6; 50 rules 3.4/1.5/1.0/0.6; 100 rules 3.4/1.5/1.1/0.7. A realistic single-instrument SR is 0.3, so you cannot validate many rules even with 30 years.
- Table 5 (p. 71): years needed on average to pass a 2-sigma t-test that SR>0 for true SR 0.2 / 0.3 / 0.4 / 0.5 / 0.7 / 1.0 / 1.5 / 2.0: 45 / 37 / 33 / 20 / 10 / 6 / 3 / 1.4 years. Negative-skew rules need about 3 more years at SR 1.0.
- Table 6 (p. 73): years to show rule A is better than rule B (SR gap rows 0.1 / 0.25 / 0.5 / 1.0; correlation columns -1 / 0 / 0.5 / 0.8 / 0.95): gap 0.1: 47/47/46/44/37; gap 0.25: 46/45/40/32/10; gap 0.5: 41/37/25/10/3; gap 1.0: 23/11/8/2.5/0.5. So ranking rules by backtest Sharpe is mostly noise.
- Pooling instruments: do not fit every instrument separately (narrative fallacy). Two of his rules with single-instrument SR 0.05 and 0.30 need about 45 years to separate; run over a portfolio they are 0.13 and 1.13 and need about 11 years. Use generic rules and fit on pooled data; fit per instrument only if a significant difference exists (rare; exception: different costs).
- Rules for effective fitting: keep it simple, fewer alternatives, no time machines, do not drop rules casually, pool data, compare equal skew, beware benchmark drift (equities and bonds had a 40-year inflation-fall tailwind; about 25% of historical performance is unrepeatable).
- His own selection procedure (p. 80+): (1) a small number of ideas (he runs 8 rules from 5 themes; starter set = trend + carry), (2) a few variations per rule picked by behaviour (speed, correlation), never by performance, (3) forecast weights by handcrafting with uncertainty about Sharpe; poor rules get lower weight but are rarely excluded. Drop a variation only if correlation with another is above 95%, or costs too high, or too slow. "Don't look at returns - yet." Returns data is reserved for setting forecast weights.
- Marginal value: trend + carry alone give about 85% of his full system's backtest performance. Diversifying over instruments beats adding rules (average correlation between rules on one instrument is higher than between instruments on one rule). Adding instruments is "tiresome" but worth more than adding rules.

### Ch 4 - Portfolio Allocation (pp. 78-100)
- Single-period Markowitz optimisation gives extreme, unstable weights (example S&P/NASDAQ/US 20y bond: bonds 68%, S&P 32%, NASDAQ 0%). Reason: it ignores the uncertainty of Sharpe estimates. Sharpe differences are rarely significant; correlation differences often are.
- Equal weights are right only if equal vol, equal Sharpe and equal correlation. Vol is equal by construction in his framework.
- Bootstrapping (App C, p. ~305): repeatedly draw random subsets of returns (sample length about 10% of history; 100-200 repeats), optimise each, average weights. No calibration needed. Beats single-period optimisation and equal weights overall. Example weights: equal 33/33/33, single-period 68/32/0, bootstrapped 53/27/20.
- Handcrafting (pp. 89-100): group similar assets bottom-up, weights from a table by correlation pattern. Table 8: one asset 100%; any two assets 50/50; any group with identical correlations equal weights; more than three assets without identical correlation, split into smaller groups. Three-asset cases (correlations AB, AC, BC -> weights A,B,C): (0,0.5,0) -> 30/40/30; (0,0.9,0) -> 27/46/27; (0.5,0,0.5) -> 37/26/37; (0,0.5,0.9) -> 45/45/10; (0.9,0,0.9) -> 39/22/39; (0.5,0.9,0.5) -> 29/42/29; (0.9,0.5,0.9) -> 42/16/42. Round correlations to nearest 0, 0.5, 0.9; floor negatives at 0. Final weight = product of weights down the group tree.
- Sharpe adjustment of handcrafted weights (Table 12, p. 96): multiply weights by a factor then renormalise. Column A (differences known with certainty, e.g. costs) for SR gap -0.5/-0.3/-0.2/-0.1/-0.05/+0.05/+0.1/+0.2/+0.3/+0.5: 0.32/0.55/0.66/0.85/0.94/1.11/1.19/1.37/1.56/1.83. Column B (uncertain estimate, more than 10 years of data or a forecast): 0.65/0.83/0.88/0.95/0.98/1.03/1.06/1.13/1.17/1.35. Column C (under 10 years of data): always 1.0, i.e. do not adjust.
- Cheating warning: handcrafting and Sharpe-adjusted weights use full-sample information. Table 14 pessimism factors (share of backtested Sharpe likely realised, for his ch-15 system): single-period optimisation in-sample 25%, out-of-sample 75%; bootstrap in-sample 60%, out-of-sample 75%; handcrafted without Sharpe in-sample 70%; handcrafted with Sharpe in-sample 65%. In-sample single-period optimisation gave a fantasy SR 0.84 and only 0.30 when done out-of-sample; bootstrap out-of-sample 0.52; handcrafted in-sample 0.54.

### Ch 5-6 - Framework overview, Instruments (pp. 103-120)
- A "bad example" system (20/40 MA cross, fixed 3% risk, trailing stop of 3% of capital) is wrong because stops and size must be based on market volatility, not account size or pain; separate rules, position sizing and vol target.
- Components: instruments -> forecasts per rule variation -> combined forecast -> vol targeting -> scaled position -> portfolio (instrument weights) -> speed/size checks.
- Instrument choice: data available, minimum sizes, understand why prices move (avoid pegged or intervened markets, e.g. CHF peg removal Jan 2015: 16% move), avoid very low volatility instruments (they need huge leverage, cost more per risk unit, jump when vol returns), prefer lower average correlation, cheap, liquid, on-exchange; watch skew.

### Ch 7 - Forecasts (pp. 121-136)
- A forecast is a scaled number, proportional to expected risk-adjusted return (so an expected Sharpe-like quantity). Binary signals are worse: forecast near zero earns less, binary costs more to trade, and the framework assumes continuity.
- Scaling: average absolute value 10; cap at +/-20 (about 5% of Gaussian observations are beyond 20). Reasons for cap: risk control, little data for extremes, extremes often mean-revert (dead-cat bounce), high forecast may just be low volatility, low vol is followed by vol spikes (Japanese bonds Jan 2013).
- No-rule rule for asset allocators: constant +10 = equal Sharpe for all assets = risk parity with continuous vol adjustment.
- Rule design checklist: simple and objective; make continuous not binary; volatility-standardise (divide by recent daily sigma in price units) so it is comparable across markets and time; recompute every bar (no separate entry/exit rules; if an exit is needed use his vol-based trailing stop); rescale by a forecast scalar so average abs = 10. His toy example: raw (open - close) / sigma has natural average abs 0.33 so scalar = 30 (he has not tested the rule).
- EWMAC trend rule (full spec in App B below): positive skew, he trusts it because of prospect theory, simple, price-only.
- Carry rule: return if prices stay unchanged (yield minus funding; futures: price gap between contracts). Negative skew, steady, occasionally blows up (central banks forced to stop). Combine trend and carry for balance.
- Rule selection: exclude variations with over 95% correlation, trade slower than a few months, or too fast for the instrument's costs (different variation sets per instrument are allowed).

### Ch 8 - Combined Forecasts (pp. 137-145)
- Combined forecast = weighted average of variation forecasts (weights positive, sum to 100%). Handcrafted example: EWMAC 16/64, 32/128, 64/256 and carry; within EWMAC group correlations 0.9 adjacent, 0.7 for 16 vs 64 -> weights 42/16/42 (Table 8 row 11); EWMAC group vs carry 50/50. Final weights 21% / 8% / 21% / 50% (Table 17).
- Forecast diversification multiplier (FDM): the weighted average of imperfectly correlated forecasts has lower variability, so multiply by FDM = 1 / sqrt(w' H w), H = correlation matrix of forecasts (floor negative correlations at 0), then cap again at 20. Example four-variation system: FDM 1.31 exactly (approx 1.27 from Table 18). Cap FDM at 2.5. Rule-of-thumb correlations: variations of one rule average 0.7 (up to 0.9); different rules same style 0.5; different styles 0.25.
- Table 18 (approximate multiplier, equal weights, identical correlation; rows N assets; columns average correlation 0 / 0.25 / 0.5 / 0.75 / 1): N=2: 1.41/1.27/1.15/1.10/1.0; N=3: 1.73/1.41/1.22/1.12/1.0; N=4: 2.0/1.51/1.27/1.10/1.0; N=5: 2.2/1.58/1.29/1.15/1.0; N=10: 3.2/1.75/1.35/1.17/1.0; N=20: 4.5/1.86/1.38/1.18/1.0; N=50+: 7.1/1.94/1.40/1.19/1.0.
- Warning: a high multiplier makes capped forecasts the norm, i.e. effectively binary; hence the 2.5 max. The multiplier is also the number of "independent bets" equivalent.

### Ch 9 - Volatility Targeting (pp. 146-162)
- Most important decision. Define the volatility target = long-run expected annualised sigma of portfolio returns, as a percentage of current trading capital (not the maximum loss; annual loss can exceed it).
- Conditions: how much can you lose; how much risk can you cope with; can you realise it (leverage, instrument natural vol); is it right for the system.
- Losses by target (Table 20, $100k capital, SR 0.5, zero skew, vol target 25% / 50% / 100% / 200%): worst daily loss each month $2.5k / $5k / $10k / $20k; worst weekly loss each year $6.9k / $14k / $28k / $55k; worst monthly loss every ten years $16k / $32k / $63k / $80k; worst day in 30 years $5.4k / $11k / $22k / $43k; 10% of the time the cumulative drawdown is at least $9.3k / $15k / $30.5k / $62k; 1% of the time $11k / $18.5k / $37k / $75k. Negative skew (Table 21) worse single days (e.g. worst daily each month $3.1k at 25%) but smaller cumulative drawdown; positive skew (Table 22) smaller single losses but longer underwater periods.
- Ten-year ruin chances (Table 23, SR 0.5): vol target 25% / 50% / 100% / 200%: chance of losing half <1% / 10% / 40% / 93%; chance of losing 90% <1% / 1.1% / 22% / 88%.
- Kelly: optimal vol target = expected Sharpe (SR 0.5 -> 50%, expected return = SR x vol target: SR 0.2 -> 4%, 0.5 -> 25%, 1.0 -> 100%, 2.0 -> 400%). Overbetting hurts more than underbetting, especially for negative skew. Use half Kelly.
- Recommended vol target (Table 25, for system builders): realistic (pessimistic) back-tested SR 0.25 / 0.40 / 0.50 / 0.75 / 1.0+ -> 12% / 20% / 25% / 37% / 50% for zero or positive skew; halve it for negative skew (6 / 10 / 12 / 19 / 25%). Never assume SR above 1.0. His own system: back-test SR 1.0 x 0.75 pessimism = 0.75 -> half Kelly 37%; he actually runs 25%.
- Semi-discretionary and asset-allocator targets (Table 26): SR 0.2 / 0.3 / 0.4 / 0.5+ -> 10 / 15 / 20 / 25%, halve for negative skew (5 / 7 / 10 / 12%).
- Do not change the percentage target after setting (meddling); only reduce once if you grossly misjudged. Start with less capital and add later.
- Roll up profits and losses: recompute trading capital daily (or at least when moves are material), so cash vol target = % target x current capital (compounding, de-risks after losses). Check at least daily if target above 15%; weekly minimum if leveraged.
- Implied vol target of "percent of capital per trade" systems (Table 27, avg 2 positions; max risk per trade 1 / 2.5 / 5 / 10 / 20%): holding 1 day -> 40 / 100 / 200 / >200 / >200%; 1 week -> 16 / 40 / 80 / 160 / >200; 2 weeks -> 8 / 19 / 38 / 76 / 152; 6 weeks -> 4 / 10 / 21 / 41 / 82; 3 months -> 3 / 7 / 13 / 27 / 53. Scale linearly with number of positions. Shows how common retail rules imply suicidal risk.

### Ch 10 - Position Sizing (pp. 163-175)
- Block value = money gained for a 1% price move of one unit; price volatility = std of daily % returns; instrument currency volatility = block value x price vol (in % points); instrument value volatility = that x FX rate to account currency. Volatility scalar = daily cash vol target / instrument value volatility (number of units that gives full target risk). Subsystem position = forecast x vol scalar / 10 (do not round yet).
- Daily cash vol target = annual / 16 (256 days).
- Vol estimate: simple SD over 25 days (default), or EWMA of squared returns with span 36 days (equivalent half-life); performance almost identical from a few days to 6 months look-back, worse beyond 6 months; EWMA formula: alpha = 2 / (L+1) (alpha = 0.054 for L=36); variance_t = alpha * r_t^2 + (1-alpha) * variance_{t-1}. Ch 15 mentions a 35-day EWMA in the daily process.
- Worked example: crude oil, 1.33% daily vol, block value $750 for a 1% move -> instrument currency vol $997.50; GBP account (USD/GBP 0.67) -> 668.325; daily target GBP 62,500 (annual 1,000,000) -> scalar 93.52 contracts; forecast -6 -> short 56.11 contracts.
- Danger: very low vol (CDS 2007, short Eurodollars, CHF peg) -> big positions -> disaster when vol returns.

### Ch 11 - Portfolios (pp. 177-190)
- Each instrument gets a subsystem (as if all capital traded just it). Portfolio position = subsystem position x instrument weight x IDM. Weights sum to 100%.
- Instrument weights by handcrafting (or bootstrapping); correlations between subsystem returns are about 0.7 x the correlation of instrument returns (dynamic strategies). Do not adjust instrument weights for Sharpe (no evidence). Rule-of-thumb correlation tables in App C below.
- IDM = 1 / sqrt(w' H w) with H the correlation matrix of subsystem returns, negative correlations floored at 0, cap 2.5. Three-asset example (bond, S&P, NASDAQ): IDM 1.41 (average correlation about 0.25).
- Crises raise correlations (2008), so IDM is a risk, hence the cap.
- Semi-discretionary: instrument weight = 1 / max number of bets; IDM = max bets / average bets; max should be at most 2.5x the average.
- Position inertia: only trade when the current position is more than 10% away from the rounded target (e.g. target 50 contracts, no trade if current is 45-55). Negligible pre-cost effect for holding periods above a few days, cuts costs materially. Round only at the very end.
- Total-position tidbit: also does not recommend more than 40 forecast units total on one asset when pyramiding (ch 13).

### Ch 12 - Speed and Size (pp. 191-214)
- Rule of thumb: trading cost should never exceed one third of a conservative pre-cost Sharpe. Example of a bad system: pre-cost SR 1.5, costs eat two thirds, after-cost 0.5; at a 20% vol target, 30% gross, 20% costs.
- Execution cost: small traders pay about half the bid-ask spread per trade (use that, be conservative); fees per ticket, per contract, percentage taxes; holding costs (rolls) ignored for speed decisions.
- Standardised cost per round trip in Sharpe units = 2 x (cost of one block) / (16 x daily instrument currency vol) = cost in annual-vol units. Examples: Euro Stoxx future 0.002 SR (1.5%/day vol, $8 per contract incl. fee); FTSE future 0.001; Australian rates futures 0.03; retail FTSE spread bet 0.01 (use as a benchmark for spread bets); low-vol bond ETF 0.08. Low-vol instruments have higher standardised cost.
- Turnover = round trips per year of an average-size position; annual cost in SR = turnover x standardised cost. From a simple backtest: turnover = (blocks traded per year) / (2 x average absolute blocks held). Sources of turnover by importance: forecast changes, volatility estimate changes, capital changes (about 3% per day at 50% target; 1% at 16%), FX, parameter changes.
- Speed limit: staunch system trader assume max pre-cost SR 0.40 -> max annual cost 0.13 SR (a third); discretionary and static investors assume 0.25 -> 0.08 SR. Max standardised cost = limit / turnover. Day trading (500+ round trips) would need cost per round trip of 0.00025 SR, a quarter of the cheapest futures, i.e. zero spread cost: effectively impossible without a proven execution edge. At 0.13 SR cost and 50% vol target the drag is 6.5% per year.
- Table 34 (limit 0.08 SR): holding 1 day -> turnover 256 -> max cost 0.00031 (no instrument); 3 days / 85 / 0.001 (cheapest futures such as NASDAQ); 1 month / 12 / 0.0067 (nearly all futures); 6.5 weeks / 8 / 0.01 (index spread bets); 3 months / 4 / 0.02; 6 months / 2 / 0.04; 1 year / 1 / 0.08; 2.5 years / 0.4 / 0.20.
- Table 35 (limit 0.13 SR, system builders): turnover 128 / 54 / 28 / 12.5 / 7.5 -> max standardised cost 0.001 / 0.0024 / 0.0046 / 0.01 / 0.017. Turnover 12.5 equals the recommended set (trend 16/32/64 plus carry).
- Weights and costs: he finds no consistent evidence that faster rules (or faster variations of a rule) have higher pre-cost Sharpe; assume equal pre-cost SR for all rules, then lower the weight of costly rules via Table 12 column A (a rule costing 0.13 SR vs average 0.03 -> multiplier only 0.95; limit makes adjustments small). Rules with turnover 65 down to 6 per year behave similarly pre-cost; below 6 turnover performance declines. Faster trend rules usually do worse because most markets do not trend at short horizons. Costs should be compared on a post-cost basis when setting the vol target.
- Volatility look-back and costs (Table 36): final turnover when you change vol look-back, starting rule turnover 0 / 1 / 5 / 10 / 12.5 / 20 / 40 / 60 -> look-back 5 weeks: 1.6 / 2.5 / 5.7 / 10.2 / 12.6 / 19.7 / 39.4 / 60; 10 weeks: 0.8 / 1.5 / 5.0 / 9.8 / 12.2 / 19.2 / 39.2 / 60; 20 weeks: 0.4 / 1.2 / 4.7 / 9.4 / 11.7 / 19.1 / 39.2 / 60. So slow vol estimation only matters for very slow systems.
- Instrument weights and costs: more expensive instruments usually are not worse after costs if turnover is below about 15 per year; so no cost-based re-weighting for slow systems.
- Large capital: execution cost not simply half spread once order exceeds depth at the touch. Small capital: minimum contract size makes positions lumpy; compute maximum position at forecast +20 = 2 x vol scalar x instrument weight x IDM; want at least 4 blocks; otherwise drop instrument or raise its weight. Most diversified portfolio consistent with that.

### Ch 13 - Semi-automatic trader (pp. 217-236) - only the stop rule matters for us
- Discretionary forecast -20..+20 plus one systematic exit: trailing stop at X daily sigmas (price units) from best price since entry, no profit target ("no evidence systematic profit targets work", markets trend). Table 38, X vs average holding period / turnover per year / max cost: X=1: 4 days, 64; X=2: 9 days, 29; X=3: 17 days, 15; X=4: 6.5 weeks, 8 (he uses this, 0.01 SR cost); X=8: 13 weeks, 4; X=10: 26 weeks, 2. A random entry plus this trailing stop was profitable in real data because of trend capture.
- Tighten stop with vol: when vol estimate doubles, stop distance doubles and position is cut roughly in half so risk per bet stays constant. Risk per bet = X x forecast x vol target / (10 x 16 x avg bets): X=4, forecast 10, 15% target, 3 bets = 1.25% of capital.

### Ch 14 - Asset allocator (pp. 237-254) - background only
- Example constraints, 7.5% vol target (limited by lack of leverage), weekly rebalancing, 20-week vol look-back, IDM 1.61, 57% of cash in bonds although weight 40%. Adjusting weights for views by Table 12 column B; keep adjustments small.

### Ch 15 - Staunch systems trader (pp. 255-280) - the key worked system
- Capital $250k, 6 futures (Eurodollar, 5y T-note, Euro Stoxx, V2TX, MXP/USD, corn); trend EWMAC 16, 32, 64 plus carry; forecast weights 21% / 8% / 21% / 50%; FDM 1.31; instrument weights 11.7 / 11.7 / 20 / 9.8 / 23.3 / 23.3 %; IDM 1.89; vol target 20%; backtest after costs (out-of-sample bootstrap) SR 0.53, times 0.75 = 0.40 realistic; half Kelly of 0.40 = 20%; 35-day EWMA vol; position inertia 10%; weekly check of carry forecast; overall turnover of combined forecast 12.5 round trips; cost of the dearest instrument 0.113 SR (< 0.13 limit).
- Table 43 turnover per rule (round trips/yr) and max standardised cost at the 0.13 limit: EWMAC 2,8: 54 / 0.0024; 4,16: 28 / 0.0046; 8,32: 16 / 0.0081; 16,64: 11 / 0.012; 32,128: 8.5 / 0.015; 64,256: 7.5 / 0.017; carry: 10 / 0.013. Only the cheapest instruments can use the fastest EWMAC.

### Epilogue (pp. 281-283)
- Be humble, simple, sceptical, pessimistic (no diversified system above SR 1.0; semi-discretionary 0.5, static 0.4), thrifty (speed limits), nervous (half Kelly, avoid low vol), diligent in design and lazy in running; do not meddle. Steady wins with no losses means negative skew not yet exposed.

### Appendix B - Rule specifications (pp. 292-299)
- EWMAC: forecast = scalar x (EWMA_fast - EWMA_slow) / (daily price-unit sigma). EWMA alpha = 2/(L+1). Slow = 4 x fast (ratio between 2 and 6 made little difference on artificial trend data, 4 chosen, checked on real data). Pairs: 2:8, 4:16, 8:32, 16:64, 32:128, 64:256 (adjacent pairs correlate 0.90; in-between pairs would exceed the 0.95 prune cutoff; slower than 64:256 has poor performance). Forecast scalars (to make average abs forecast = 10, measured over many futures without looking at performance): 10.6, 7.5, 5.3, 3.75, 2.65, 1.87 respectively. Cap at +/-20. Daily data, no weekends.
- Carry: raw carry = annualised expected return if nothing changes (price units) divided by annualised price-unit sigma (= 16 x daily sigma) = a Sharpe-like number; forecast scalar 30; cap 20. Futures: (price of contract traded minus price of nearer contract) / years between contracts, or next-minus-current if trading the nearest. Equities: dividend yield minus funding; CFD funding = average of long and short financing; FX: interest in foreign currency minus domestic funding; spread bet: (spot - bet level)/time to maturity. Check weekly (turnover rule of thumb 10 round trips per year).
- Early loss/profit taker "A and B" system (not recommended for live use): position = $100k / instrument value vol; reverse at A sigma profit or B sigma trailing stop.

### Appendix C - Rule-of-thumb correlations (pp. 305-309)
- Instrument returns, super classes: rates-equities 0.1, rates-FX 0.1, equities-FX 0.1, commodities-FX 0.25, equities-volatility 0.6 (vol shown as short), FX-vol 0.2; bonds-STIR 0.5; metals-agri 0.2; energy-agri 0.25; energy-metal 0.35; emerging vs developed: bonds 0.35, equities 0.5, FX 0.15; same region equities/bonds/FX/vol different country 0.75; same country equities different industry 0.70, same industry 0.80; bonds same country by maturity 2y-5y 0.80, 2y-10y 0.65, 2y-30y 0.50, 5y-10y 0.85, 20y-30y 0.90.
- Trading rule returns on one instrument: different styles 0.25; same style different rules 0.5. EWMAC variation correlations (Table 57, p. 309), order 2:8, 4:16, 8:32, 16:64, 32:128, 64:256: row 4:16 = 0.90 with 2:8; row 8:32 = 0.60, 0.90; row 16:64 = 0.35, 0.60, 0.90; row 32:128 = 0.20, 0.40, 0.65, 0.90; row 64:256 = 0.15, 0.20, 0.45, 0.70, 0.90 (adjacent 0.90, two steps apart 0.60-0.70, further apart 0.15-0.45).
- Bootstrap sample length: about 10% of history; 100-200 repeats; block bootstrap if time dependence matters.

### Appendix D - Formulas (pp. 311-312)
- Forecast scalar = 10 / (average absolute raw forecast measured across many instruments and years). Diversification multiplier = 1 / sqrt(w' H w), floor negative correlations at 0. Vol: SMA of 25 days or EWMA with alpha = 2/(L+1), L=36.

## Topic tags

**trend**
- EWMAC six speeds 2:8 to 64:256, forecast scalars 10.6 to 1.87, cap 20; prefer at least three speeds because speeds cannot be ranked; turnover 54 down to 7.5 per year; fast speeds only for very cheap instruments. Trend rules are positive skew; he gets Sharpe benefit mainly from diversification across instruments.
- Random entry + vol-scaled trailing stop (X=4 sigma, no profit target) captured trends and was profitable.
- Most markets do not trend at short horizons, so faster trend rules generally have worse pre-cost Sharpe.

**breakout / mean-reversion / momentum**
- No dedicated treatment of breakout; he says breakouts, MA crossovers and oscillators capture the same trend behaviour, so one family is enough. Mean reversion: only one toy range-trading example (GBPUSD +/-5% around 1-year mean) not recommended; relative value is negative skew and crowded. Extremes often mean-revert, hence the forecast cap.

**intraday / sessions / seasonality**
- Book is daily data. Says fast (under a day) trading needs near-zero costs; day trading unprofitable for nearly all amateurs. Seasonality only mentioned as forced-trader effects (tax year end).

**volatility**
- Everything is divided by recent daily sigma (25-day SMA or 36-day EWMA, alpha=0.054); stops, forecasts, sizing and costs all use it. Avoid pegged and very low vol markets; vol targeting reduces size when vol rises.

**stops-and-exits**
- No profit targets; only a trailing stop at X x daily sigma from the best price; X sets holding period (Table 38). Exits for systematic rules happen by forecast change (continuous), not by separate exit rules. Stops must reflect market vol, not account size or pain.

**position-sizing / risk**
- Vol target (% of current capital), half Kelly of a pessimistic Sharpe (Tables 25, 26), volatility scalar, forecast/10, IDM, position inertia 10%, max position at forecast 20 must be at least 4 blocks. No change of target while running; capital rolled up daily.

**testing-and-robustness / overfitting**
- Tables 3-6, 14 above; ideas first; no performance-based selection of rules; expanding or rolling out-of-sample only; pool instruments; compare equal skew; apply a pessimism factor (65-75%) to backtest Sharpe, and treat 1.0 as ceiling; trust costs more than pre-cost Sharpe; huge history is needed to prove a rule works (20-45 years at SR 0.2-0.5).

**costs / execution**
- Standardised cost formula, turnover, speed limit 1/3 of 0.4 SR (0.13) or of 0.25 (0.08), Tables 34-36, half-spread assumption, assume today's costs even for old data (old costs were higher so fast rules may only look good).

**psychology / discipline**
- Meddling, overconfidence, loss aversion; objective rules; do not look at P/L to change risk; start small.

**portfolio / diversification**
- Instruments matter more than rules; handcrafting tables; IDM cap 2.5; subsystem correlation = 0.7 x instrument correlation; diversification is "the only free lunch"; Sharpe doubles with four uncorrelated bets.

## Testable ideas

(All of these assume daily bars resampled from M1; none holds intraday positions unless noted. Swap cost applies to overnight holds; his slow rules hold weeks to months, so swap must be net of carry.)

1. ★ **Carver combined-forecast engine (framework test)** - For each instrument (XAUUSD, GBPUSD, GBPJPY, NAS100, US500) compute daily-close forecasts for EWMAC 16/64, 32/128, 64/256 (optionally 8/32), price-unit sigma by EWMA(36) of daily returns, scalar 3.75/2.65/1.87 (5.3 for 8/32), cap 20 each; equal weights or handcrafted (21/8/21 with carry, or about 42/16/42 for three speeds alone); multiply by FDM from the measured correlation matrix (floor 0, cap 2.5), cap 20; position = forecast x (daily vol target in cash / instrument value vol) / 10; rebalance only if target differs from current by more than 10%; vol target 10-20% of capital (half Kelly of a pessimistic SR). Source ch 7-11, App B/D, pp. 121-190, 292-312. Claimed evidence: pooled backtests on 40+ futures, rolling SR about 0.5 for 6 instruments, 1.0 for 45; trend + carry about 85% of his full system. Fit: good for method (continuous forecast, no stop-and-reverse, no ATR stop) but swap on longs/shorts of FX/indices must be included; only 5 instruments, high correlation of the two indices and of gold/FX = small IDM; cost is tiny relative to turnover 8-12 per year. Differs from strategy 4: continuous scaled sizing, three speeds blended, slower speeds (up to 256-day), no hard stop, position inertia, vol target sizing, forecast cap.
2. ★ **Slow-only EWMAC blend and swap-as-carry** - Add a carry forecast using the broker financing rate: for FX, interest differential (swap long minus swap short from the FTMO swap table) / (16 x daily sigma) x 30, cap 20; for indices, dividend yield minus funding (use swap rates as proxy; check weekly). Combine 50% carry / 50% trend as in his example. Source App B carry. Evidence: he says carry is a major earner and diversifies trend (correlation 0.25 between styles). Fit: our data has swap rates in the cost model, not futures term structure; FX carry has negative skew (CHF Jan 2015); gold carry is funding cost only (negative) so the rule would mostly short gold. Differs: strategy 4 had no carry; carry is paid by swap instead of costing it.
3. ★ **Forecast-weighted vote of our failed strategies** - Treat each previously tested strategy (session zone sweep direction, NY open sweep, no-wick, gap fade, ORB, trend following) as a forecast: convert signal strength to a number in -20..+20 normalised to average abs 10 (e.g. signal / R or distance / ATR scaled), combine with equal or handcrafted weights using the correlation of their daily R streams, FDM, cap 20, size by vol scalar. Source ch 8, p. 137-145. Evidence: Carver shows equal blends beat selection (SR 0.33 vs 0.07 for best-of-last-year, 0.20 random); weak edges may add only if pre-cost SR is positive, otherwise no. Fit: poor if each component has negative net edge; useful as a test of whether combining adds anything beyond the best component. Differs: tests combination rule rather than a new signal.
4. ★ **Vol-scaled trailing stop with random entry baseline** - Random daily entries (or entries from any weak signal) exited only by a trailing stop X x daily sigma from the best price since entry (X in {1, 2, 3, 4, 8}), no profit target, size by vol scalar; use as the null benchmark that any entry rule must beat (he reports random entry + this exit is profitable on real data due to trend capture, Table 38 holding periods 4 days to 26 weeks). Source ch 13, p. 224, footnote 142. Fit: good as a null model for our Monte Carlo (random entries); intraday version possible by using 15m-1h sigma. Differs from strategy 4: no entry rule, exit and size purely vol-based, no reversal.
5. **Instrument-diversification multiplier check for FTMO** - Run the same single-rule subsystem on each instrument, compute subsystem correlation matrix, compute IDM = 1/sqrt(w'Hw) and compare realised portfolio vol to target; test with real 2008-like crisis correlations (stress: raise correlations). Source ch 11. Fit: tests whether five symbols give a worthwhile multiplier (indices 0.75-0.9 correlated, gold/FX moderate); likely IDM 1.2-1.4 only.
6. **Cost-based speed limit filter** - For each instrument and rule compute standardised cost = 2 x (half-spread + commission) / (16 x daily currency vol) and turnover; reject any rule with turnover x standardised cost above 0.13 SR (a third of 0.4). Use for intraday strategies too: scale 16 to sqrt(bars per year) if using intraday vol. Source ch 12. Fit: directly applicable to our cost model; will immediately rule out fast variants.
7. **Position inertia and vol-estimate speed as a cost test** - Re-run any continuous-position strategy with 10% inertia and with 25-day vs 100-day vol look-back to see how much cost falls (Table 36). Cheap and low-risk.
8. **Volatility target as 'trade size' for prop-firm limits** - Choose the account vol target from Kelly: half of pessimistic SR (e.g. SR 0.4 -> 20%, negative skew halve) and compare to FTMO 5% daily / 10% total loss limits via Monte Carlo of the daily P/L (Tables 20-23 give reference loss distributions at 25-200% targets). Source ch 9.

## Warnings / pitfalls

- Backtests are optimistic: never expect more than 65-75% of backtested Sharpe (Table 14), and 25% of historical returns for equities and bonds came from a unique disinflation. Treat SR above 1.0 as impossible for any diversified system; single-instrument SR 0.3-0.4 is typical.
- Selecting from many rules or variations all but guarantees a false winner (Tables 3-4); rankings of rules by Sharpe need decades (Tables 5-6). Decide variations by behaviour (speed, correlation), not by returns; use equal weighting or handcrafted weights, adjust only for costs.
- Implicit overfitting through only testing ideas you already know work; narrative fallacy (a good story is not proof).
- Do not fit per instrument; pool across instruments.
- Over-betting: vol target above half Kelly of a pessimistic SR ruins accounts (ten-year chance of losing half at 100% target is 40%, at 200% it is 93%). Negative skew needs half the risk.
- Overtrading: costs above one third of SR make a system unwise; a retail-cost system holding a week needs 83% a year pre-cost to break even (Intro example). Day trading: cost per round trip must be below about 0.00025 SR.
- Low-volatility instruments and pegged markets: high leverage, high standardised cost, sudden blow-ups.
- Negative skew hides in high-Sharpe, high-hit-rate backtests (carry, option selling, relative value, market making); crowded trades and margin calls are the failure mode.
- Binary or discontinuous signals and separate exit rules do not fit the framework; stops must be set in market sigma, not in capital terms.
- Large diversification multipliers let capped forecasts behave like a binary rule and underestimate risk when correlations jump in a crisis; cap at 2.5; floor negative correlations at zero.
- Do not meddle: changing risk targets after losses, taking profits early, manual overrides destroy performance; changes in parameters also create trades (costs).
- Old data had higher costs than today; fast rules that look good historically may be unexploitable.
