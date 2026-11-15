# Idea universe and work framework, 2026-11-15 (Claude Fable 5.2, advisory)

Backlog: `research/idea_backlog/2026-11-15-fable-ideas.csv` (335 rows, FB-001..FB-335, 22 families). Read before
writing: `knowledge/topics/cost-wall.md`, `research/ledger.csv` (140 rows), `docs/HANDOFF.md`, the four reports of
2026-11-14/15, my notes of 2026-11-11 and 2026-11-14, the `knowledge/ideas.md` overview table, the SMT stub in
`docs/confluences.md`, `strategy/registry.py`. **No data was looked at, no code of the project was run, no web page
was opened. Every paper, book, URL, fee and prop-firm rule is from memory and UNVERIFIED;** Opus opens each before
relying on it. Every bp figure marked "guess" is mine. `prior_pct` = my chance that the row survives its first
screen (for data / method rows: that it is useful). Nothing here is a recommendation to trade.

Row types: 210 strategy, 20 filter, 34 method, 26 data, 14 prop-mechanics, 31 reading. **99 rows have priority 5:
most of them are listed only because the brief asks for a fair list; they overlap a falsified family or fail on
power or cost arithmetic and should not be run.** About 100 rows are worth a look; about 40 screens cover them.

## 1. Summary (10 lines)

1. **Breadth on Binance stays the best place** (XS-CRYPTO, CRYPTO-FLOW): the only pass (I-78) is there, power is
   free (300+ perps), costs are known, and three free data sets are still unused: daily-speed flow, spot flow,
   and the long/short account ratios and open interest in the `metrics` files (FB-001, 003, 004, 005, 007).
2. **Make the one passed strategy usable before finding a second:** capacity, maker fills (FB-273, 274), a
   liquid-only frozen variant (FB-017) and a crypto prop firm that trades real perps (FB-261). That is the
   shortest route from an existing result to goal 1.
3. **Daily, no-swap, cheapest-cell CFD ideas with a published mechanism we never tested:** the overnight index
   premium (FB-107..109), the 2024 noise-band intraday momentum with its gamma conditioning (FB-199, 201), and
   intraday two-leg trades on NAS100 / US30 / US500 / GER40 at 2-4 bp for both legs (FB-052..059).
4. **Share CFDs are the only untouched asset class with breadth on FTMO** (59 names). The overnight-to-intraday
   reversal (FB-112, 113) is daily, cross-sectional and can be screened on free daily data. Costs are unknown:
   the census (FB-111) decides the whole family.
5. **Signal stacking** (FB-244): the cost wall says several effects are real at 1-3 bp gross. They add when they
   agree in the same window, and cost is paid once. Cheap to count; fair evidence only forward or on the test.
6. **SMT and ICT can be answered cheaply and fairly with two tools,** not 50 strategies: a two-symbol event
   study (FB-078) and a level-touch null model with breadth (FB-126, 127). I expect most concepts to match
   random levels; the priors are 1-5 % and say so.
7. **Prop mechanics still has open, certain-value work:** payoff shape (FB-258), rule table across firms
   (FB-259), funded phase (FB-265). No edge, but it sets the target every other row is judged against.
8. **Low promise, stated:** anything weekly or rarer on one symbol (power), anything multi-day on CFDs (swap),
   every single-symbol bar pattern, clock windows, macro nowcasts, seasonals. They are in the csv, closed.
9. **The binding constraint is multiplicity, not ideas.** 335 rows at t 3 would give about one false pass by
   luck. The framework below caps looks per family and counts test-period uses.
10. **Needed from the owner:** five decisions (end of this file); no purchase is required for the first 30 steps.

## 2. Framework

### 2.1 Taxonomy (22 families, rows)

| Group | Families (rows) | Venue | What decides the family |
|---|---|---|---|
| Crypto breadth | XS-CRYPTO (22), CRYPTO-FLOW (17), CRYPTO-EVENT (12) | Binance (goal 2; crypto prop firm = goal 1) | threshold already 3.5 (4 looks in crypto_xs_factors) |
| Two instruments | PAIRS (26), SMT (18) | FTMO cheapest legs, intraday | one tool each; two-leg cost 2-4 bp |
| CFD breadth | XS-CFD (15), SHARES (15) | FTMO | censuses FB-109, FB-111 |
| Practitioner concepts | ICT (34), RETAIL (12), MICRO (14) | FTMO | null-level tool FB-126 |
| Flows and events | EVENT (13), VOL (11), FLOW (10), SEASON (6) | FTMO | power line per row; GEX data check FB-210 |
| Slow premia | TREND (8), CARRY-MACRO (10) | futures / swap side | swap census FB-228; futures data |
| Method | META (14), EXEC (6), OOB (10) | all | no market look or forward only |
| Mechanics and inputs | PROP (15), DATA (16), READ (31) | n/a | no market look |

### 2.2 Work order (waves) and why

| Wave | What | Rows | Why here |
|---|---|---|---|
| 0 | Rules and tools before any look: family budget ledger, canaries, dose-response and pooling outputs, the three censuses (one read-only MT5 call), Binance coverage listing, GEX file check | FB-255, 287, 246, 247, 252, 228, 111, 302, 291, 210 | certain value, zero multiplicity, unlocks or closes about 60 rows |
| 1 | Strategy 20 realism and venue; Binance breadth sorts | FB-273, 274, 259, 261, 017, 001, 005, 004, 003, 007 | only place with a pass; power free; cost known |
| 2 | Daily CFD rows in the cheapest cells | FB-109, 107, 108, 199, 201, 200, 052-055, 059, 078-080, 095, 244, 179 | fit the pass map (daily, +2.5-5 bp needed); no swap or one night |
| 3 | Shares, if the census allows | FB-290, 112, 113, 114, 115 | breadth on FTMO; free daily data for the screen |
| 4 | ICT / retail concepts through the null-level tool | FB-126, 127, 149, 137, 138, 128, 131, 146, 158 | closes about 40 rows in one pass; the owner asked for a fair test |
| 5 | Pooled events and slow rows that pass a power line | FB-186, 190, 066, 215, 028, 029, 032, 040 | few events: only pooled, only after the power line |
| - | Priority-5 rows | 99 rows | not run; kept so they are not re-proposed |

Order inside a wave: (1) can it be tested on data we have, (2) cost cell against the guessed gross, (3) power
(events a year x breadth), (4) prop fit, (5) does one script serve several rows.

### 2.3 Batching (one script, many rows)

| Script (new or extended) | Serves |
|---|---|
| Cross-sectional sort on perps (the I-78 screen, generalised: sort key, horizon, universe) | FB-001..016, 018, 021 |
| Pooled event study on perps (date-clustered) | FB-023, 025, 028, 029, 031, 032, 040..044, 176 |
| Two-leg intraday tool (FB-052) | FB-053..060, 062, 064, 065, 073, 098, 099, 280 |
| SMT event table (FB-078, built on the two-leg tool) | FB-079..095, 158, 182 |
| Level-touch null model + breadth event study (FB-126, 127) | FB-128..157, 160, 161, 173, 174, 178 |
| Generic event-screen tool (directions row 23) | FB-186..192, 215, 242 |
| Noise-band screen (one script, three cells) | FB-199, 200, 201, 175, 250 |
| Daily-OHLC share screen | FB-112, 113, 114, 123, 124 |
| Challenge simulator options | FB-258, 260, 265..268, 271 |

### 2.4 Per-idea pipeline (unchanged repo rules, made explicit)

1. **Card** in `knowledge/ideas.md` from the csv row: rule, mechanism, kill criteria written before any data.
2. **Arithmetic gate:** cost cell vs halved published (or guessed) gross. Below cost = closed without a look.
3. **Power line:** MDE at t 3 from the power map (or sd x 3 / sqrt(N) for new cells). Halved effect below MDE
   = closed without a look, unless the row can be pooled.
4. **Screen** on development data only (CFDs before 2021-09-14; crypto 2020-2023), one look, frozen rule,
   date-clustered t, halves, doubled costs, dose-response by signal decile (FB-246), pooled estimate (FB-247),
   correlation with existing streams (FB-252). Each new tool first reproduces a ledger result (FB-287).
5. **Gates** in a `docs/strategy-*.md` spec only after a passed screen; build by the usual route.
6. **One-time test,** once, variant frozen, per the `Mode` rule. Pass or fail goes to the ledger and HANDOFF.
7. **Forward log** with a sequential boundary (FB-254) for every pass and for right-sign survivors.

### 2.5 Multiple-testing budget

Existing rule (harvest framework section 6): |t| >= 3.0 up to 10 screened ideas in a family, 3.5 up to 50, 4.0
above; at most 5 screens per batch; a changed rule is a new row. Proposed additions:

| Family | Looks already in the ledger | Budget from this backlog | Threshold | Closes when |
|---|---|---|---|---|
| XS-CRYPTO (crypto_xs_factors + reversal) | 4 (I75, I78, I79, I80) | 6 sorts | 3.5 | budget spent, or 4 in a row under t 1.5 |
| CRYPTO-FLOW / EVENT | 4 (I72, I76, I81, I69) | 5 event studies | 3.0, then 3.5 | 3 falsified in a row |
| PAIRS | 2 killed + 4 lead-lag | 5 cells in one run | 3.5 (cells of one tool) | no cell with gross > half its cost |
| SMT | 0 | 6 configs in one run | 3.5 | with-SMT minus control <= cost in all |
| ICT / RETAIL / MICRO levels | S01-S03, H15, S11 (large) | 1 null-model pass (descriptive) + 3 event rows | 4.0 | null model shows no concept above random |
| SHARES | 0 | 4 | 3.0 | census cost > guessed gross, or 2 falsified |
| VOL / FLOW (index intraday momentum family) | S06, S07, H02, H06 | 3 cells in one run | 3.5 | this is the family's last look |
| XS-CFD overnight | SC2 (check) | 2 | 3.0 | net <= 0 incl. financing |
| EVENT | S12, H03 | 2 pooled | 3.0 | second falsification (two-falsification rule) |
| TREND, CARRY-MACRO, SEASON | closed on CFDs | 0 until data or census changes | n/a | n/a |

About 40 screens in total. Expected false passes at these thresholds: about 0.05 (two-sided alpha 0.0027 at
t 3.0, 0.0005 at 3.5). The count is printed at the top of each report (FB-255).

**Test-period uses are counted too.** The crypto test period (2024+) has been used by I-73 and I-78; each further
one-time test on it is another draw from the same weeks. Proposal: the ledger gets a column "test-period use
number per venue"; from the 5th use the one-time test needs t >= 3.0 instead of the development-gate default.
This changes a rule, so it is the owner's decision.

### 2.6 Stop rules

- No rescue variants. Rows marked POST-HOC (FB-026, 043) may only be judged on data nobody has seen.
- A family closes at its budget or its close condition; the remaining rows are set to "closed with family".
- HANDOFF Open 9 (pause goal-1 signal research after K = 10 falsified screens with no pass) fits this backlog
  as written: count wave 2-5 screens. Binance work and prop mechanics continue.
- A descriptive census or null model counts as one look for its family and never as a pass.
- A pass is a reason for a spec, not a finding (existing rule).

## 3. Hedge-fund strategy map

| Class | What a retail CFD / perp account can copy | What it cannot, and why | Backlog rows |
|---|---|---|---|
| Statistical arbitrage, pairs, baskets | Intraday two-leg trades on the cheapest index / FX legs; residual reversion on 59 share CFDs; sector pairs; perps cross-section | Thousands of names at 0.2 bp cost, intraday netting, borrow: our two-leg cost is 2-30 bp and multi-day pays financing on both legs (P01, P02) | FB-052..077, 112..114, 121 |
| Cross-sectional factors (momentum, value, carry, quality, low volatility, reversal) | On perps: flow, positioning, momentum, low beta, size (weekly, funding instead of swap). On shares: daily overnight / intraday sorts | Monthly factor holds on CFDs: financing equals the premium (I-51). Value and quality need fundamentals and long holds | FB-001..021, 103..106, 112, 124, 125 |
| Relative value / basis | Perp vs spot carry, quarterly basis, cross-exchange funding (exchange money, not prop) | Bond, swap-spread and convertible relative value: no instruments | FB-035..037, 070 |
| Event-driven | Scheduled macro and central-bank releases pooled; earnings on share CFDs; crypto listings, unlocks, delistings | Merger arbitrage, activism, index-add trading in single names: capital, borrow, multi-week holds | FB-040..047, 115..117, 186..192 |
| Volatility selling / buying | Proxies only: fade of the implied daily move, noise-band momentum, quiet-day reversion; real option selling only on Deribit | No listed options at FTMO; the premium itself cannot be collected with CFDs | FB-199..209, 050, 180 |
| Risk-premia harvesting | Overnight equity premium on index CFDs (one night of financing); positive-swap carry; trend + carry on real futures | Diversified premia need 30+ futures or real assets; CFD financing eats multi-week holds | FB-107, 108, 229, 221, 237, 125 |
| Market making / liquidity provision | Passive quoting on wide-spread perps; shock-reversal rules (being paid for immediacy) | Queue position, rebates, colocation; on CFDs we always cross the broker's spread | FB-038, 025, 098, 099, 121, 181, 273 |
| Flow and positioning | Dealer-gamma sign from a free daily file; retail long/short ratios (Binance history, FX forward collection); index-review auctions | Prime-broker and options-flow data; closing-imbalance feeds | FB-005, 006, 171, 201, 210, 215, 284 |
| Global macro and nowcasting | Rate-spread and surprise rows as cheap falsification; prediction-market odds | Discretionary macro has no rule; monthly horizons have no power in our sample | FB-197, 196, 230..236 |
| CTA trend and modern variants | Breadth trend on perps; Carver rule set on real futures at a track-record venue | CFD trend: killed by swap (S04, I-51); futures props forbid overnight holds (UNVERIFIED) | FB-009, 220, 221, 264 |
| Seasonality of flows | Only daily ones have power; all listed ones are closed | Monthly / yearly: no power (I-67, I-70) | FB-238..243, 216..218 |
| ML signal ensembles | Equal-weight composites and one pre-registered boosted model, breadth first on perps | Alternative data, thousands of features, 0.2 bp execution | FB-021, 244, 249, 250 |
| Multi-strategy portfolio construction | K weak uncorrelated streams, netting, staggered windows, forward boundaries | Internal crossing and leverage of a pod shop | FB-245, 252..254, 266 |

## 4. Two instruments and SMT: the best 20

Why these pairs: both legs are in the cheapest cost cells (US30 1.0, GER40 1.1, EURUSD 1.0, USDJPY 1.2, NAS100
1.7, US500 2.2, XAUUSD 2.3 bp), the hold is intraday (no swap: what killed P01 / P02), and the event is daily
or pooled so the power map allows 2-6 bp. Where one leg is expensive (silver, DXY, megacaps) it is used as the
signal only.

| # | Row | Pair | Form | Why it could differ from the ledger |
|---|---|---|---|---|
| 1 | FB-052 | any | tool | reproduces L15 first; everything below is a config |
| 2 | FB-078 | any | SMT tool | SMT exists only as a two-line spec; the control (sweep with confirmation) is the test |
| 3 | FB-079 | NAS100 / US500 / US30 | SMT trigger at the session extreme | S02 tested the sweep alone |
| 4 | FB-080 | same | follow the stronger leg | mirror hypothesis, same run |
| 5 | FB-095 | same + EURUSD / GBPUSD | continuous SMT (z-score) | dose-response instead of a binary swing |
| 6 | FB-053 | NAS100 vs US30 | morning rotation continues | first intraday spread test; 2.7 bp |
| 7 | FB-054 | NAS100 vs US30 | extreme rotation reverts | second cell |
| 8 | FB-055 | NAS100 vs US500 | residual z-score | half-life check first |
| 9 | FB-059 | four US indices | agreement = trend day | breadth as a filter, never used |
| 10 | FB-060 | XAUUSD vs EURUSD, USDJPY | fade gold's idiosyncratic H1 shock | S11 used raw shocks |
| 11 | FB-083 | XAUUSD / XAGUSD | silver signals, gold trades | L17 died on silver's 30 bp |
| 12 | FB-081 | EURUSD / GBPUSD | SMT at London / NY extremes | S01 on GBPUSD had no second symbol |
| 13 | FB-082 | EURUSD / DXY inverted | SMT | DXY as signal only |
| 14 | FB-057 | GER40 vs US30 | overlap-hours spread | L14 was close-to-open |
| 15 | FB-088 | S01 / S02 trade lists | SMT as a filter (descriptive) | costs nothing; honest only as a difference test |
| 16 | FB-086 | 8 pairs pooled | daily-swing SMT, 3-5 day hold | larger move per event; pooled for power |
| 17 | FB-091 | NAS100 vs 8 megacaps | breadth SMT | index high made by few names |
| 18 | FB-066 | AUDUSD / NZDUSD (AUDNZD) | range reversion, days | large move per trade; I-59 is also unblocked (FB-067) |
| 19 | FB-114 | share sector pairs | overnight gap spread converges intraday | pooled over pairs, daily |
| 20 | FB-085 / FB-093 | BTC / ETH; BTC vs breadth | SMT on perps; breadth divergence | flow and breadth are where crypto worked |

Not in the 20, stated in the csv: oil vs CAD / NOK (FB-062, 063: L15 already measured 1.2 bp against 1.7),
gold / silver ratio (FB-061: only reopens if silver's cost has fallen), WTI / Brent and metal ratios (cost and
swap), crypto vs NAS100 and MSTR vs BTC (FB-071, 283: power), yen crosses vs indices (FB-064, 092: low prior).

## 5. ICT / smart-money concepts

All of these describe one mechanism: resting stop and limit orders at obvious levels are liquidity for large
traders. The only peer-reviewed support I know is Osler's work on order clustering in FX (FB-323, UNVERIFIED).
Our falsified families S01 (sweep + structure shift + zone entry, 17,742 trades), S02, S03 and H15 tested this
mechanism with tight stops on single symbols. A new test is meaningful only if it changes the **measurement**,
not the stop: a timed exit, breadth across 30 symbols, a matched random-level control, or a second-symbol
condition. Two tools do that (FB-126, 127).

| Concept | Testable rule | New vs falsified families | Row |
|---|---|---|---|
| Liquidity sweep / stop hunt, PDH / PDL raid | trade through the level, close back, timed hold | S01 / S02 with a timer, breadth and a control | FB-128 |
| Judas swing, session high / low raids | Asian or London range raid, reversal | core of S01: counted in that family | FB-129, 130 |
| Power of three (AMD), midnight / 08:30 open | false move below the open, reclaim, hold to 16:00 | new as a rule; one look | FB-131, 132 |
| Weekly profile, TGIF | weekly low by Tuesday; Friday retrace | base rate vs random walk first | FB-133, 156 |
| Killzones, macros, quarterly theory | clock windows | SC1 / SC2: closed | FB-135, 136, 153 |
| Silver bullet | FVG in 10:00-11:00 as an event with a timer | S03 family; low prior | FB-134 |
| FVG, order block, breaker, mitigation, BPR, unicorn | first return to the zone | null model: does the zone hold more often than a random zone | FB-137..141 |
| Premium / discount, OTE | position in the range; 62-79 % retracement | forward return by range position; ratio vs neighbours | FB-142, 143 |
| Market structure shift (2022 model) | sweep, displacement, FVG entry | exactly S01: closed | FB-144 |
| Turtle soup | false 20-day break, 3-day hold, pooled | H15 had 38 trades; second and last look | FB-145 |
| Candle range theory | H4 / D1 sweep and close back inside | key-reversal family; breadth + control | FB-146 |
| IPDA ranges, daily bias | 20 / 40 / 60-day extremes; close beyond PDH | equals trend or its fade: closed | FB-147, 152 |
| NWOG / NDOG, opening range gap | gap as magnet | study 11.2, S05: closed or null model | FB-148, 154 |
| Draw on liquidity, equal highs / lows | equal highs are exceeded more often than single highs | new as a measured claim; a target rule if true | FB-149 |
| Displacement | strong move before the setup | a column, not a strategy | FB-151 |
| SD projections | reversal at -2 / -2.5 / -4 multiples | null model vs neighbours | FB-155 |
| SMT | section 4 | new (spec stub only) | FB-078..095 |
| News-day sweeps | spike fully retraced, follow the retrace | cell of the macro screen | FB-157 |
| Breadth of sweeps | market-wide vs single-symbol stop run | new condition | FB-158 |
| Retail neighbours | supply / demand, Wyckoff, indicators, squeeze, harmonics, grid | closed or one null-model config | FB-160..170 |

Honest expectation: the null model shows touch-and-reverse rates within noise of random levels for most
concepts (as study 11.2 did for gaps). The rows with the best chance are the conditional ones (FB-149, 158,
079), at 4-8 %.

## 6. Data sources, venues, reading

**Data (all URLs UNVERIFIED; check terms before any scrape; downloads follow the `Mode` rule).**

| Source | What | Rows it unlocks |
|---|---|---|
| FTMO MT5 server (have) | swap / cost / history-depth census for all 166 symbols | FB-228, 111, 302 and about 40 dependants |
| data.binance.vision `futures/um/daily/metrics`, `aggTrades`, `bookTicker`, `premiumIndexKlines`; `spot/monthly/klines` | open interest, long/short ratios (from about 2021-12), trades, spot taker flow | FB-004..008, 027, 028, 038, 273 |
| squeezemetrics.com/monitor/dix (csv), cboe.com VIX family history | dealer gamma, dark-pool index, implied volatility | FB-200..205, 210 |
| Alpaca market data free tier; stooq.com/db/h; Yahoo daily | US share minute bars 2016+, daily OHLC | FB-112..124 |
| sec.gov EDGAR full index | earnings dates | FB-115..117 |
| dukascopy.com historical data feed | independent ticks and spreads from 2003+ | FB-289 (checks the spread table) |
| fred.stlouisfed.org, alfred.stlouisfed.org, fiscaldata.treasury.gov, treasurydirect.gov | yields, vintages, auctions | FB-191, 197, 233..235 |
| public.bybit.com, OKX / Deribit / Coinbase / Upbit APIs | funding, options, premium, Korean volume | FB-030, 031, 037, 049, 050 |
| DefiLlama, CoinGecko, Coin Metrics community | unlocks, categories, market cap | FB-015, 018, 040 |
| Myfxbook / OANDA / IG retail sentiment | retail positioning, forward collection only | FB-171, 284 |
| Polymarket / Kalshi APIs | event odds | FB-196 |
| ForexFactory / investing.com calendars | consensus values (terms unclear) | FB-187, 295 |
| stooq futures, EIA; one paid futures set | futures prices with rolls | FB-221, 237, 297, 298 |

**Venues to look at (rules UNVERIFIED; FB-259 builds the table).** CFD firms: FTMO Swing and 1-Step, The5ers,
FundedNext, E8, Funding Pips, Alpha Capital. Futures firms: Topstep, Apex Trader Funding, My Funded Futures,
Tradeify, Take Profit Trader (most use trailing loss lines and forbid overnight holds). Crypto firms trading
exchange perps: Breakout, HyroTrader, Crypto Fund Trader (question: are small perps listed, are weekend and
week-long holds allowed). Shares: Trade The Pool. Track-record model without a target: Darwinex Zero.

**Top 25 to read** (csv rows FB-305..FB-335 give the reason and what to extract; "rules" = how likely the
source contains testable rules):

| # | Source | Rules |
|---|---|---|
| 1 | Kakushadze & Serur, *151 Trading Strategies* (2018) | high |
| 2 | Pedersen, *Efficiently Inefficient* (2015) | medium |
| 3 | Zarattini, Aziz & Barbon 2024 "Beat the market"; Zarattini, Barbon & Aziz 2024 (stocks in play) | high |
| 4 | Lou, Polk & Skouras 2019 "A tug of war"; Bogousslavsky 2021; Hendershott, Livdan & Roesch 2020 | high |
| 5 | Boyarchenko, Larsen & Whelan 2023 "The overnight drift"; Bondarenko & Muravyev 2023 | high |
| 6 | Baltussen, Da, Lammers & Martens 2021 (in the project); Barbon & Buraschi 2020 "Gamma fragility" | high |
| 7 | Osler 2003, 2005 (stop-loss and take-profit clustering) | high |
| 8 | Liu, Tsyvinski & Wu 2022; Liu & Tsyvinski 2021 | high |
| 9 | Carver, *Advanced Futures Trading Strategies* (2023) | high |
| 10 | Avellaneda & Lee 2010 "Statistical arbitrage in the US equities market" | high |
| 11 | Isichenko, *Quantitative Portfolio Management* (2021) | medium |
| 12 | Chan, *Quantitative Trading* (2009), *Machine Trading* (2017) | high |
| 13 | Ilmanen, *Expected Returns* (2011), *Investing Amid Low Expected Returns* (2022) | medium |
| 14 | Harris, *Trading and Exchanges* (2003) | low (mechanisms) |
| 15 | Narang, *Inside the Black Box*; Tulchinsky, *Finding Alphas*; Kakushadze 2016 "101 Formulaic Alphas" | medium |
| 16 | Gatev, Goetzmann & Rouwenhorst 2006; Do & Faff 2010; Krauss 2017 | high |
| 17 | Vidyamurthy, *Pairs Trading* (2004); Pole, *Statistical Arbitrage* (2007) | medium |
| 18 | Sinclair, *Volatility Trading* (2013), *Positional Option Trading* (2020) | medium |
| 19 | Bennett, *Trading Volatility* (2014) | medium |
| 20 | Bouchaud, Bonart, Donier & Gould, *Trades, Quotes and Prices* (2018) | medium |
| 21 | Grimes, *The Art and Science of Technical Analysis* (2012) | high |
| 22 | Bellafiore, *One Good Trade* (2010), *The Playbook* (2013) | medium |
| 23 | Krohn, Mueller & Whelan 2024 "FX fixings and returns around the clock" | high |
| 24 | Harvey, Liu & Zhu 2016; Harvey & Liu 2020; McLean & Pontiff 2016 | method |
| 25 | Blogs: Robot Wealth, Quantpedia (free part), Alvarez Quant Trading, Quantified Strategies; SqueezeMetrics white papers; Hoffstein 2020 "Liquidity cascades"; ICT's own 2022 mentorship videos for definitions | high / medium |

Already in `knowledge/` (not repeated): Aronson, Aziz, Carver 2015, Chan 2013, Coulling, Davey, Hougaard,
Kaufman, Lopez de Prado, Masters, Pardo, Volman.

## 7. Top 30 to run first, in order

1. FB-255 + FB-287: family budget ledger and tool canaries (rules before looks).
2. FB-274: capacity and impact of Strategy 20 at $10k / $100k / $1m.
3. FB-273: maker-fill model on aggregated trades (10 -> about 4 bp if not adversely selected).
4. FB-259: rule table across CFD, futures, crypto and share prop firms.
5. FB-261: can Strategy 20 run at a crypto prop firm (symbols, holds, loss rules), then its pass map.
6. FB-228 + FB-111 + FB-302: one read-only MT5 census (swap, cost, depth for 166 symbols; shares).
7. FB-291: coverage listing of the Binance metrics / spot / trade files.
8. FB-001: daily taker-flow sort (I-78 at 1-day speed; 7x the events).
9. FB-005: retail long/short account ratio contrarian sort (data never used).
10. FB-004: spot minus perp taker flow.
11. FB-003: absorption sort (flow not confirmed by price; two cells).
12. FB-109 -> FB-107, FB-108: overnight vs intraday census on 16 indices, then the overnight premium incl. financing.
13. FB-210 / FB-293: gamma file check (start date, look-ahead).
14. FB-199: noise-band intraday momentum, frozen from the paper (last look of the index-momentum family).
15. FB-201 + FB-200: the same run split by gamma sign; the fade cell.
16. FB-052 -> FB-053, FB-054, FB-055: two-leg tool, then US rotation and residual cells.
17. FB-078 -> FB-079, FB-080, FB-095: SMT event table on the US triad, both legs, graded by size.
18. FB-179: variance ratio by volatility / news / gamma regime (signal-free).
19. FB-244: count how often gross-right effects overlap; freeze the equal-weight stack.
20. FB-258: payoff-shape study in the challenge simulator.
21. FB-290 -> FB-112, FB-113: share data check, then the overnight-to-intraday reversal on free daily OHLC.
22. FB-126 + FB-127: level-touch null model and breadth event study.
23. FB-149, FB-137 / 138, FB-128, FB-131: equal highs, FVG, PDH / PDL raid, power of three through those tools.
24. FB-010 (+ FB-009, FB-011): the owner's decision on HANDOFF Open 5 (crypto momentum, one-time on 2024+).
25. FB-017 + FB-254: liquid-only Strategy 20 frozen; forward ledgers with boundaries.
26. FB-059: four-index agreement day.
27. FB-060: gold residual to the dollar.
28. FB-186 (+ FB-157): macro release first move, pooled; follow and retrace cells.
29. FB-028 + FB-029: funding extremes pooled over all perps.
30. FB-265 + FB-260: funded-phase policy; pass map per rule set.

Next in line: FB-115 (earnings-day momentum), FB-066 (AUDNZD), FB-032 (pump-onset), FB-025 (idiosyncratic shock),
FB-284 (retail positioning collector), FB-007 (open interest quadrants), FB-190 (central-bank days).

## 8. Not checked

- No source, paper, URL, free-tier limit, fee or prop-firm rule was opened or verified; several papers are cited
  from memory by author and year only. Titles may be slightly off.
- No data look: every gross figure is a guess unless it quotes the ledger; the two-leg costs are sums of the
  power-map single-leg costs and ignore the spread at the cash open, where share and index spreads are widest.
- I did not open `docs/research-log.md`, the SC1 / SC2 cell lists, the ORB and I-78 output files or the harvest
  task list. So I do not know whether SC2 contained the overnight window (FB-107), whether the ORB test cell's
  volume split exists (FB-172), whether I-78 reports legs separately (FB-020), or whether directions rows 14,
  16, 23, 24 are done.
- FTMO share CFD costs, hours and history depth; index CFD financing per night; the meaning of the MT5 spread
  column; whether the Binance `metrics` files really start in 2021-12; whether the gamma file is free and
  point-in-time: all unknown, each has a data row.
- The 59 share names: I assumed 46 trade in US cash hours; ASML and AZN may be the European lines.
- Whether negative-skew sizing, parallel accounts or crypto-firm weekly holds are allowed by any firm's terms.
- The budget in 2.5 uses my own grouping of ledger rows into families; Opus should re-count from `ledger.csv`.
- I did not check this backlog against the 140 ledger rows mechanically; overlaps are named from reading.

## Decisions needed from the owner

1. Test-period use counting (2.5): adopt, yes / no (changes a rule).
2. HANDOFF Open 5 (crypto momentum one-time run) and with it FB-009, FB-011, FB-220.
3. Downloads: Binance metrics / spot / aggTrades; gamma and VIX files; US share minute bars (free tier account).
4. A scheduled daily collector for retail positioning (FB-284) and, if wanted, the crypto prop-firm route (FB-261).
5. Books (optional): FB-305..312, FB-319..322, FB-327, FB-331. Paid futures data stays "no" unless you say so.
