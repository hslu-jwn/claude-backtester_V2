# Post-mortem of the research program and a map of where edges can still live

Claude Fable 5.2, advisory, 2026-11-16 (last session). Part 1 of 2.

Read: the context pack, `research/ledger.csv` (189 data rows), my 2026-11-14 directions list, `docs/HANDOFF.md`,
the newest ~150 lines of `docs/research-log.md`, `docs/strategy-crypto_flow.md` (result table), the power budget
map, the pass map, the prop mechanics report, the Strategy 20 prop decision package, the family budget table and
the 335-row backlog (keyword search only). No data was looked at, no code run except one row count of the
ledger, no web page opened. Numbers marked "mine" are arithmetic from ledger figures. Everything about outside
venues, papers and data sets is from memory and marked UNVERIFIED. This is research analysis, not a
recommendation to trade or to buy anything; money decisions are the user's.

## 0. The short version

1. The ledger fits one two-number model. An effect is **profitable** only if the signal's hit quality (IC, about
   0.02-0.05 for every real effect measured here) is larger than **c = round-trip cost / the instrument's sd over
   the hold**. It is **provable** only if IC x sqrt(independent name-periods) >= 3. Crypto weekly sorts have
   c ~0.006 and ~9,000+ name-weeks. Every FTMO CFD cell has c 0.03-0.10 and 80-1,700 periods. That is the whole
   difference; the mechanisms on CFDs are real (the gross sign is right nearly every time) and exactly cost-sized.
2. There is **one** independent survivor (weekly taker-flow sort: I-78 = Strategy 20; I-83 and FB-017 are the
   same bet), plus one weak right-sign stream (I-73 carry). Multiple testing is not the threat to it; tails and
   regime are (2022-23 earned about zero).
3. The gates do reject real small effects (about 9 right-sign rows at t 1.5-2.9 against about 4 expected by
   chance), but none of them would pass a challenge alone. What is missing is a "shelf" between falsified and
   passed, and a single pre-registered combination.
4. The survival properties hold in three unexplored places on free data: wide US share universes traded as
   real shares through the auctions, free flow data for shares (daily short-sale volume), and a second crypto
   venue with public flow (independent replication of Strategy 20's signal). All three need a venue other than
   FTMO.
5. Goal 1 on FTMO CFDs with a real edge: about 3-5 %. Shift the weight.

## 1. Pattern of survival

### 1.1 What the ledger contains (counted)

| Group | Rows | Outcome |
|---|---|---|
| Harvest rows (HV-*) | 85 | never reached data: untestable, unfetchable, needs data; led to ~4 screens, 0 survivors |
| Closed without a data look (power 9, arithmetic / closed family 21) | 30 | all closed on my or Opus's guessed sizes |
| Data looks (screened 34, dev_tested 23, tested 8, falsified 1) | 66 | 2 independent right-sign results with t >= 3 in two separate periods (I-78; I-83 is its twin) |
| Method / forward / diagnostic / draft | 8 | n/a |

### 1.2 Gross edge against cost, by family (ledger numbers; ratio and sd columns are mine)

| Family (rows) | Gross per bet | Cost per bet | Gross / cost | Gross in sd of the bet | Independent dates in development |
|---|---|---|---|---|---|
| Practitioner / ICT intraday on CFDs (S01-S03, S09, I-88, I-91..I-94) | -0.05 to +0.03 R; -0.8 to +2.5 bp; FVG +0.2 bp over random levels | 1.4-2.0 bp; 0.05-0.2 R at tight stops | < 0.5 mostly, best 1.6 (I-91) | ~0 | 1,000-1,700 days |
| Published intraday flow on CFDs (H01, H02, H06, H07, S08, L14-L17, I-85, I-89) | +0.9 to +3.7 bp (0.01-0.07 R) | 1.6-15 bp | 0.2-1.7 (only F1a EURUSD 2.9) | 0.01-0.07 | 600-1,700 days |
| Calendar / rare events on CFDs (H03, H04, H09, I-67, I-70, I-71, Gotobi) | -9 to +20 bp; I-71 +11.7 | 2-6 bp | I-71 4.3, others < 1 or wrong sign | I-71 ~0.3, Gotobi ~0.03 | 41-413 events |
| Multi-day CFD holds (S04, I-51, P01, P02, I-87, C2) | I-51 gross Sharpe -0.13; P01 +209 bp | swap: I-51 -1,924 bp in total; P01 333 bp; I-87 3.5-5 vs 2.8 | < 1 | n/a | 18-80 |
| Share CFDs, daily cross-section (I-96) | +10.1 bp a day (gross t 4.44) | 16.1 bp | 0.63 | 0.08 | 2,944 days |
| Crypto intraday / single-name events (I-72, I-76, C3, L18) | +2.3 to +7 bp | 10-20 bp | 0.2-0.7 | ~0.05 | 1,700-5,100 clusters |
| Crypto weekly cross-section, 17-37 perps (I-73, I-73R, I-75) | +83 to +158 bp (I-75 -127) | 20 bp | 4-8 | 0.1-0.2 | 81-82 weeks (dev) |
| **Crypto weekly cross-section, all perps (I-78, I-83, FB-017, I-84, I-97, I-79, I-80)** | +26 to +191 bp; survivors +165 to +191 | 20 bp | 1.3-9.5; **survivors >= 8** | **survivors 0.27-0.35** | 186 weeks dev + 147 test |
| Crypto spot-hedged carry (I-98) | +45 bp a week | 33 bp | 1.4 | n/a | 186 weeks |

### 1.3 The five structural properties

**P1. Cost ratio c = round-trip cost / sd of one instrument over the hold must be below ~0.01-0.02.**
Every real effect in the ledger has about the same quality per instrument-bet: 0.03-0.07 sd (I-85 0.065, F1a
0.066, I-96 0.08 gross, I-76 0.05, Strategy 20 about 0.04 per coin-week if the legs hold ~50 coins each: mine).
An IC of 0.04 on a 35 bp intraday index or FX bet is 1.4 bp: exactly the 1-3 bp the ledger keeps measuring. The
same IC on a coin-week with sd ~1,700 bp (UNVERIFIED guess) is ~70 bp per leg. Cost decides which one is an edge:

| Cell | Cost (bp) | Instrument sd over the hold (bp) | c | Verdict in the ledger |
|---|---|---|---|---|
| Small / mid perp, 1 week, Binance taker | ~10 a side-turn | ~1,700 (guess) | ~0.006 | survivors |
| US500 / NAS100 / FX major CFD, 6 h | 1-2 | 30-87 | 0.02-0.05 | break-even: right sign, net <= 0 |
| FX cross CFD, 6 h | 2-4 | 30-37 | 0.06-0.12 | dead (F1X) |
| Index CFD, 1 week incl. swap | ~2 + 12-15 | 170-240 | ~0.08 | dead (I-51, I-87) |
| Crypto CFD, 1 week incl. swap | ~65-115 | 900-1,200 | 0.07-0.1 | dead (I-95, HV-T0020) |
| BTC / ETH perp, 1 h, taker | 10 | 118-129 | 0.08 | dead (I-72, C3) |
| Share CFD, 1 day, long-short | 16 | ~125 | 0.13 | dead (I-96) |
| US large / mid-cap share, real, 1 day through the auctions | 1-4 (UNVERIFIED) | 150-200 | 0.01-0.02 | untested |
| US share, real, 1 week | 3-6 (UNVERIFIED) | 350-450 | ~0.01 | untested |

**P2. Breadth inside each bet: 50+ loosely related names, giving ~5,000+ independent name-periods.**
t ~ IC x sqrt(N_eff x T). At IC 0.04, one symbol with 1,700 daily bets gives t ~1.6: this is why the CFD
right-sign rows sit at t 1.5-2.5 and never 3. I-73 with 17 perps x 82 weeks: predicted t ~1.5, measured 1.30.
All perps x 186 weeks: predicted ~3-4, measured 3.24. The 34 FTMO CFDs are about 6-8 independent bets
(4 US indices, 3 European, USD pairs, JPY crosses, 2 metals, 2 oils), so no cross-section of them can do this.

**P3. The signal uses information that is not the instrument's own price: a direct footprint of a trader who is
constrained.** Taker flow and funding are such data; every CFD idea had price and clock only. In the ledger a
real mechanism predicts the *sign* (F2 right in 5 of 5 indices, F1X 4 of 4, fix 4 of 6, I-71 and Gotobi in every
sample) while practitioner patterns show no sign at all (ICT levels = random levels, no-wick 24 of 24 negative).
Mechanism gives the sign, c gives the profit, breadth gives the proof. A forced counterparty alone is not enough.

**P4. Limited arbitrage capital: a venue or segment that funds with 0.2 bp costs do not work.** Small perps
(capacity of a few hundred thousand USD), retail-dominated flow. All 34 CFD underlyings are the most-arbitraged
instruments there are, which is why their real effects are worn down to exactly the institutional cost level,
i.e. below ours. I-96's gross edge on large-cap shares fading to negative in 2019-21 is the same thing.

**P5. No financing drag at the horizon where P1 holds.** P1 pushes the hold to days or weeks (sd grows with
sqrt(time), cost does not). On FTMO that horizon pays swap (index 2.4-2.9 bp a night, crypto -30 % a year), which
puts c back to 0.07-0.1. Perp funding is two-sided and small, real shares pay nothing on the long side.

One more observation about sourcing, not a market property: the only survivor came from **a data set nobody had
screened** (taker volume already on disk), labelled ORIGINAL, with the sign not known in advance. 85 harvested
strategy ideas and ~40 published-effect rows produced nothing tradable. Data-first beat idea-first.

## 2. Biases in the process

### 2.1 Is it letting false ones through?

| Risk | Evidence | Size |
|---|---|---|
| Multiple testing across 190 rows | 66 data looks at one-sided t 3 expect ~0.09 false passes; Strategy 20 has t 3.24 and t 3.76 in two disjoint periods, liquid top-100 3.64 / 3.06, and the daily version (I-82) has the same gross per day (+15.8 bp x 7 = ~110 bp a week, gross t ~2.8: mine) | **small** for Strategy 20 |
| "Pooled t" used as the pass statistic | I-73: development killed at t 1.30, tested anyway, test t 2.93 < 3.0, "pooled t 3.08", replication on 20 unseen perps failed (t 1.05). I-83: test t 2.85 < 3.0, "pooled t 4.56". Whether pooled t was pre-registered: UNVERIFIED | **real leak.** By the program's own gate I-73 is not a survivor; HANDOFF treats it correctly (forward log only), the context pack does not |
| Twins counted as survivors | I-83 (corr 0.83) and FB-017 (subset) are the same bet as I-78 | independent survivors: **1**, not 4 |
| Tail-driven mean, t assumes thin tails | capped at +-30 %: +56-58 bp, t 1.8-1.9; capped at +-50 %: +78-97, t 2.4-2.6 | **the main risk**: 40-60 % of the edge sits in weeks where fills, short squeezes and auto-deleveraging are least like the backtest |
| Regime dependence hidden by the "both halves > 0" gate | development halves +327 / **+2**; liquid +336 / +41; Bybit-listed 2021-11..2023 +41-45 (t 1.1-1.2); profit switched from the long leg (dev) to the short leg (test) | **real**: in a quiet / bear regime the expectation is ~0-40, not 92 |
| Test period reuse | 2024+ used for I-73, I-78, I-83 plus 3 diagnostics (FB-017, FB-020, S20BY) | moderate; the forward log is now the only clean test |

My forward estimate for Strategy 20: **+60 to +90 bp a week** net (the package's "fair" +92 is the top of my
range), yearly Sharpe ~1.0-1.3 on its own; probability the forward net is > 0: ~65-70 %; >= +50: ~45 %.

### 2.2 Is it killing real ones?

Yes, in one specific way. For an effect whose expected t is 2, the chance of t >= 3 is 16 %; at expected t 2.5 it
is 31 %. Right-sign rows with t 1.5-2.9 and net > 0: I-71 (2.16), I-76 (2.50), I-84 (1.76), I-98 (1.84), F1a
(~2.4 in development), Gotobi (three samples positive), I-73 test (2.93), S06 test cell (~1.5), H13f (+0.136 R,
50 trades). About 9 against ~4 expected by chance in 66 looks (rough count, mine). So some are real small
effects. But their sizes (+0.02-0.04 R, +5-9 bp, yearly Sharpe 0.2-0.6 each before shrinkage) mean none is a
strategy alone. The loss is not the kills; it is that (a) a t 2.2 right-sign row is filed as a "falsification"
and counts toward closing its family, and (b) the combination of such rows was never evaluated as one hypothesis.

Other candidates for wrongly killed edges, checked:

- **Cost model too harsh?** No. Measured CFD spreads were 1.5-2.25x the model on GBP pairs and indices; Binance
  fills measured 9.9 bp against 5 assumed. Costs are, if anything, still kind. The cost wall is a venue fact.
- **Wrong horizon?** Partly. Nearly all CFD work was intraday (c 0.03-0.1) or multi-day with swap (c ~0.08).
  There is no horizon on FTMO where c < 0.02. Not a bias: a property of the venue.
- **Closed on a guess.** 30 rows were closed without a look on "halved guess < MDE", where the guess was mine or
  Opus's. My guess for the flow sort was 20-60 bp a *day*; the real number is ~165 a *week*: guesses for original
  ideas are worth little, and the rule would have closed the only survivor had it been carded weekly at 50-100 bp.
  The closures most exposed: FB-006 / FB-008 (positioning and open-interest sorts: same data type and universe as
  the survivor; MDE 141 bp on 104 weeks against a family whose realised gross effects are +26 to +191, median ~70).
  At the family median they are still underpowered alone (expected t ~1.1-1.5), so the closure stands as a
  standalone test, but they belong in a pooled or composite design, not in the bin.
- **T-20 (resting limit entries)** is still UNTESTED after five days as "carded". On FTMO a limit fills only when
  the quote comes to it, so adverse selection is built in; my prior that it saves anything is ~10 %. Close it by
  arithmetic or run it once; do not leave it open.

### 2.3 What I would change, concretely

1. **Three verdicts, not two.** FALSIFIED (net <= 0, or wrong sign, or gross below cost with the gross interval
   excluding cost); UNPROVEN-POSITIVE (net > 0, same sign in every independent sample, 1.5 <= t < 3.0); PASSED.
   Only FALSIFIED counts toward closing a family. UNPROVEN-POSITIVE rows go automatically to the shelf (section 4).
2. **Replace "halved guess vs MDE" by the two numbers** for every new card: c for its venue-horizon cell, and
   name-periods. Cells with c > 0.03 are closed for all price and flow signals without carding (table in 1.3).
   For ideas with no published size, use the family's own realised effect distribution, not a guess, and write
   the pass probability on the card; park below ~15 %, do not call it closed.
3. **No statistic may pass a gate unless it was written in the card** (pooled t). Relabel I-73 and I-83:
   "test t < 3.0: not confirmed alone; pooled evidence only".
4. **Tail and regime gates for cross-sectional books:** (a) the +-50 % capped version keeps the sign and at least
   half the mean; (b) no half below 25 % of the full mean (Strategy 20's development would have been flagged:
   +327 / +2); (c) report the median period and a t on winsorised returns next to the plain t.
5. **Alpha spending on the crypto test period:** t 3.0 for uses 1-3 (spent), 3.3 for the 4th, 3.5 from the 5th;
   diagnostics on a spent period are never quoted as evidence for a new variant.
6. **Report every survivor shrunk:** selection (best of ~8 sorts) and regime, not just the measured mean.
7. **Honour K = 10.** Goal-1 signal screens on the 34 CFDs stop. Nothing in sections 1-2 gives a reason to resume.
8. **Scouts and harvests look for data sets, not strategies:** free, wide (100+ names), non-price (flow,
   positioning, short sales, liquidations), with 3+ years of history. That is what part 2 should rank highest.

## 3. The map: unexplored territory that follows from P1-P5 (owned or free data only)

Priors are my chance of "passes its own development and test gates". "c" and power lines are mine; anything
about outside data or venues is UNVERIFIED and is a job for the scouts.

| # | Territory | P1 cost ratio | P2 breadth / power | P3 non-price data | P4 limited arbitrage | P5 no drag | Plausible effect vs MDE | Cheapest first screen | Prior |
|---|---|---|---|---|---|---|---|---|---|
| A | **Independent replication of the flow signal on a second venue with public trades** (Hyperliquid: on-chain fills, liquidations, positions by address; ~150 perps, from 2023; access path UNVERIFIED) | yes (~0.006) | ~150 names x ~130 weeks; long-short sd ~475: MDE ~125 bp at t 3; as a *replication* the bar is t 2 = ~83 bp | yes, the strongest: signed flow plus who holds what | yes | yes | Strategy 20-sized (+100-165 gross) would show at t 2-3.5 | Signal-free: can full trade history be downloaded free, how many perps, how many weeks. Then the frozen Strategy 20 rule on that venue's own flow and prices, one look, kill at t < 2 | 25 % that it replicates; high value either way |
| B | **Wide funding-carry sort with the Strategy 20 harness**, excluding the 37 perps already seen (I-73 used 17, I-73R 20; no wide funding sort is in the ledger or the backlog by keyword: UNVERIFIED that none was run) | yes | 200+ unseen names x 186 weeks dev; MDE ~105 at t 3 if sd ~475 (carry legs may be wilder) | yes (funding) | yes | yes | I-73 +112-138, replication +63: expected t 1.8-3.5 | Data on disk. One sort variable (7-day mean funding), quintiles, weekly, 20 bp, section 2.3 gates. Second look of `crypto_carry_xs`: closes the family either way | 20 % |
| C | **One pre-registered crowding composite** (flow + funding + open-interest change), pooled dev + test weeks from 2021-12, threshold t 3.5 | yes | 251 weeks: MDE(3.5) ~105 | yes | yes | yes | family median ~70 gross: expected t ~2 | Only after B; equal-weight z-scores, no fitting. This is where FB-006 / FB-008 / FB-244 belong. Forward-only if B fails | 12 % |
| D | **US shares, wide (500-1,500 names), daily open / close effects traded as real shares through the opening and closing auctions** (overnight-intraday tug of war, end-of-day reversal: ledger rows HV-T0097-2, HV-T0098-1 are "parked: needs data", and I-96 found gross t 4.44 on 33 names killed only by 16 bp CFD cost) | 0.01-0.02 if auction fills cost ~1-4 bp (UNVERIFIED: Alpaca order types, auction cut-off times) | 1,400 days; a 100-a-side book has sd ~40 bp a day: MDE ~3 bp a day | no (price only) | **weak**: I-96 faded to negative 2019-21 on large caps; mid caps unknown | yes long, small borrow fee short | 2-10 bp a day gross (guess) vs 2-4 cost: marginal | Signal-free first: does Alpaca serve delisted names (survivorship), are daily open / close the auction prints, how many names 2016+. Then I-96's frozen rule on the wide universe, 2016-2021-09, real-share cost | 10 % |
| E | **Free flow data for shares: FINRA daily short-sale volume per symbol** (UNVERIFIED: free files from ~2010; DIX on disk is the index-level aggregate of the same data), weekly sort on the short-volume ratio | ~0.01 | 1,000 names x 300 weeks; sd ~125 bp a week: MDE ~22 bp | yes | weak in large caps | small borrow fee | published ~27 bp a week (2000-04 sample, UNVERIFIED) halved 13: expected t ~1.8; mid caps may be larger | Scout: files exist, history, coverage. Then a power line with real sd; one look | 8 % |
| F | **Leveraged single-stock ETF rebalance into the close** (2x TSLA / NVDA / MSTR products, 2022+; flow = assets x leverage x (leverage - 1) x day return: computable before the close) | real share ~0.02; FTMO share CFD ~0.1 | ~15 names, big-move days: ~600 date clusters, sd ~90 bp: MDE ~11 bp | yes, the purest forced flow | weak (widely known) | intraday | index version measured 0.5-1.3 bp (F2); single names have far larger flow / volume: guess 10-30 bp on days with flow > 3 % of closing volume | Scout: ETF asset history free? Signal-free: flow / closing-volume ratio per name and day; stop if rarely > 1 %. Needs its own split (mechanism did not exist before 2021-09) | 10 % |
| G | **Retail positioning collector** (FB-284) for FX, gold, indices | n/a | forward only; ~2 years before a test | yes | n/a | n/a | n/a | Start the daily snapshot now; every week not stored is lost | certain to be cheap, 5 % to matter |
| H | Delisting / monitoring-tag drift on Binance (FB-041; announcement dates scrapeable: UNVERIFIED) | yes | ~120 events, sd ~2,000 bp: MDE ~550 bp | partly (exchange forces holders out) | yes | funding can spike | post-announcement drift unknown; needs > 550 bp | Power line with real event count first | 5 % |

**Looked at and closed by the properties, without a card:**

- **FX cross-section** (P03 is still an untested draft): 8 currencies = 7 independent bets, no flow data, deepest
  market, ~50 trades a year. 1,000 weeks of histdata give MDE ~10 bp a week (Sharpe ~0.65) against published G10
  momentum / carry of ~0-0.3 after 2008. Fails P2, P3, P4. Close P03 by arithmetic.
- **Index CFD cross-section:** ~4 independent bets. Fails P2.
- **Any crypto sort faster than ~3 days:** an 8 h long-short bet has sd ~105 bp against 20 bp cost (c ~0.19);
  I-82 shows the daily gross is the weekly edge at the same rate per day, so speed adds cost and no edge. The only
  lever is lower turnover (a hold-until-rank-leaves buffer; forward variant only, saves maybe ~10 bp a week).
- **Sector-ETF rotation (11 ETFs), DIX / GEX timing of one index, VIX term structure, stablecoin or ETF flows
  into BTC:** one or two bets per date. Fail P2.
- **Bybit / OKX as extra universes for the same coins:** same bets, no new breadth (venue transfer is shown).
- **The 46 FTMO share CFDs with minute bars:** P1 fails at 8-16 bp (I-96; I-99's result is not in the repo yet:
  UNVERIFIED). More minute-bar screens on these 46 names are the same cost wall again. The Alpaca download is far
  more valuable as *daily bars for a wide universe* than as minute bars for 46 names.
- **Exchange futures (goal 2):** c is fine (ES day ~0.007) but no data, the most efficient market there is, and
  diversified trend + carry has Sharpe ~0.3-0.6: a long-run own-money allocation, not a prop strategy (section 4).

## 4. The portfolio angle

### 4.1 The prop challenge is a Sharpe target (closed form, mine; no daily-loss rule, thin tails)

With yearly Sharpe S and yearly volatility v, a 2-step (+10 / -10, then +5 / -10) is passed with ~83 % when
v ~9 % x S, and then takes about **T ~1.65 / S^2 years**. Smaller size raises the pass chance and the time.

| Net yearly Sharpe of the whole account | Volatility for ~83 % | Time to pass |
|---|---|---|
| 0.4 | 3.6 % | ~10 years |
| 0.7 | 6.4 % | ~3.4 years |
| 1.0 | 9 % | ~1.65 years |
| 1.3 | 12 % | ~1 year |
| 2.0 | 18 % | ~5 months |

It agrees roughly with the Strategy 20 package (15 % a side: ~96 % in ~1.6 years; 25 %: 86 % in ~0.8-1 year).
"A stream needs +0.05 R at 300 trades" is the same statement: 0.05 x sqrt(300) / 1.2 = Sharpe ~0.7.
Check it once against the house simulator; if it holds, it replaces the pass-map lookup.

### 4.2 What the existing streams add up to

| Stream | In-sample yearly Sharpe | My forward estimate | Venue | Note |
|---|---|---|---|---|
| Strategy 20 (flow sort; I-83, FB-017 are the same stream) | 2.2 (test) | 1.0-1.3 | Binance / Bybit perps | 2022-23 ~0 |
| Strategy 19 (carry, I-73) | 1.3 (test), 0.5 (replication) | 0.4-0.6 | same | weekly corr with S20 0.06 |
| I-84 spot-minus-perp flow | ~0.9 | ~0.3 | same | corr 0.58 with S20: adds ~nothing |
| I-98 hedged carry | ~0.9 | ~0.3 | spot + perp | different account type |
| Gotobi G1 | ~0.3 | 0.15-0.3 | FTMO | ~62 trades a year |
| I-71 index-review close | ~0.6 | ~0.3 | FTMO | 7 events a year |
| F1a EURUSD, ORB test cell | 0.7 | ~0.1 | FTMO | failed pre-sample / fading |

- **Crypto account:** sqrt(1.1^2 + 0.5^2) = **Sharpe ~1.2** if the two are truly independent: a pass in roughly
  1.1-1.6 years at ~10-11 % volatility. The spec's in-sample mix (Sharpe ~2.6, t 4.30) is the upper bound, not
  the expectation. To reach Sharpe 2 it would take four independent Sharpe-1 streams; rows A-C can add at most one.
- **FTMO account:** the whole shelf is Sharpe ~0.4 at best: ~10 years. It cannot be mixed with the crypto book
  (different venue, crypto CFD swap). **There is no legitimate FTMO portfolio in this ledger.**
- **"Balances itself across regimes" is not true yet.** Both crypto streams look like bull / pump-regime streams
  (S20 halves +327 / +2 / +120 / +174; I-73 halves +2 / +274, replication -19 / +146). A weekly correlation of
  0.06 can hide a shared slow factor. Cheap check on existing lists, no new look at signals: correlation of
  26-week block sums and a per-year table of both; and the joint worst 10 % of weeks. Nothing in the ledger earns
  in a quiet crypto regime.

### 4.3 Combining without p-hacking

1. Write the combination card **before** computing any joint statistic: inclusion rule mechanical (PASSED, or
   UNPROVEN-POSITIVE with every independent sample positive at doubled costs); one stream per mechanism cluster
   (correlation > 0.5 on development = same stream); weights = equal risk from development volatility only;
   no optimisation, no regime switch, no filter (a regime gate on a stream is a new look at that stream).
2. Shrink each stream's mean before sizing (PASSED x 0.6-0.7; UNPROVEN x 0.3-0.5); size the account so the
   shrunk portfolio sits at the volatility of table 4.1.
3. The combination is **one** hypothesis, judged once on forward data with the O'Brien-Fleming boundary already
   registered (FB-254); additions enter only at pre-set dates (every 26 weeks), never after a good run.
4. Regime balance is a result to report (do the weak periods overlap?), not something to engineer.

### 4.4 Mapping onto the firms

| | FTMO CFDs | Crypto prop on Bybit (HyroTrader / CFT; rules as read by Opus 2026-11-15) |
|---|---|---|
| Loss rules | 5 % daily, 10 % static, no time limit | same shape; plus 5 % aggregate low-cap cap, 40 % best-day rule (Hyro), reverse-trading rule to confirm (CFT) |
| Horizon with c < 0.02 | none (swap) | weekly long-short is allowed, weekend holds |
| Streams that fit | shelf only, Sharpe ~0.4 | S20 top-100 tranches (+ S19 once its boundary confirms) |
| Binding risk | the cost wall | the daily 5 % rule under simultaneous wicks (pass 96 % on close marks, 44 % on the wick bound at 15 % a side); payout honoured or not |
| Income if funded (mine) | n/a | ~0.8 x Sharpe x volatility x balance: at Sharpe 1.1 and 5-9 % volatility ~4.5-8 % of the balance a year; small unless the account is large |

The prop wrapper adds capital but its loss limits force the book to ~5-9 % volatility, so the firm's leverage is
not what a Sharpe-1 high-volatility book lacks. Whether a funded account beats the same book on own capital
without a daily rule depends only on account size against own capital and on payout risk: the user's question.

## 5. Is goal 1 realistic? (one honest paragraph)

Not with this data and this cost level. FTMO offers no cell with c below ~0.02: intraday the best cells break
even against real, correctly-signed effects, and every longer hold pays swap. The 34 CFDs are 6-8 independent
bets on the most-arbitraged instruments in the world, the only data is their own price, and 66 data looks plus
1,452 calendar cells found nothing above cost. I put the chance of finding a rule-based FTMO CFD stream with
net >= +0.05 R at >= 300 trades a year on owned or free data at **3-5 %** for any further three months of this
effort, and the chance that a real edge passes an FTMO challenge within 12 months at **under 5 %** (a pass by
luck is ~30 % per attempt and proves nothing; the challenge's option value at zero edge is a separate, terms-bound
money question from my 2026-11-14 list, not research). The crypto prop route is the only one with evidence:
Strategy 20 real and net positive going forward **~65-70 %**; a 2-step passed within 24 months given a purchase
**~50 %** (edge real x ~90 % pass at 15 % a side, plus slow luck otherwise, minus the 1.6-year median); payouts
then honoured as modelled **~70 %** (UNVERIFIED guess). A second independent stream from rows A-F within three
months: **~20-25 %**; a whole-book forward Sharpe >= 1.3 over two years: **~20 %**. Weight I would give the
program: ~10 % goal 1 (forward logs of the shelf, venue facts, nothing else), ~50 % crypto (replication A, wide
carry B, tail and regime checks, the forward log), ~30 % wide US shares on a real-share venue (D, E, F; a new
venue is the user's decision), ~10 % method (section 2.3). Goal 2 futures stays an own-capital allocation
question that waits on bought data.

## 6. Not verified

- Every outside fact: Hyperliquid data access and depth, FINRA short-volume files, Alpaca coverage of delisted
  names and auction order types, leveraged single-stock ETF assets, published effect sizes quoted from memory,
  all prop-firm terms beyond what Opus recorded.
- The coin-week sd of ~1,700 bp and the leg size of ~50 behind the per-name IC; N_eff per family; the share
  long-short sds in section 3. They are orders of magnitude, not measurements.
- Whether "pooled t" was pre-registered for I-73 / I-83; whether a wide funding sort was run outside the ledger;
  I-99's result (not in the repo); the Gotobi t values (the ledger gives R, not t).
- The closed form in 4.1 against the house simulator (daily-loss rule, fat tails, tranching ignored).
- The count "9 right-sign rows vs 4 expected" is a rough hand count and mixes development and test rows.
