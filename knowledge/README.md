# Trading knowledge base

What the trading books in `C:\Users\justi\Documents\00_Literature\Trading` teach, in our own words, kept
so new strategies can be built and tested from it. Started 2026-10-14; grows with every new book.

**This is background, not rules.** Trading rules live only in `docs/` (CLAUDE.md › Specs are the source
of truth). An idea from here becomes a rule only when the user picks it and it is written into a spec.

## How to use it
- **Looking for a strategy idea?** → [ideas.md](ideas.md) (ranked backlog with IDs, status, sources).
- **Planning or judging a backtest?** → [topics/testing-and-robustness.md](topics/testing-and-robustness.md)
  (checklist for every run).
- **Need what the books say about a subject?** → one of the topic files below (merged across books,
  with source refs).
- **Need the detail or a page number?** → the book notes in `books/`.

## Topics (synthesis across books)
| File | Covers |
|---|---|
| [testing-and-robustness.md](topics/testing-and-robustness.md) | IS/OOS, walk-forward, parameter plateaus, robustness %, shocks, trial log + deflated Sharpe, CPCV / PBO, Davey gates, matched monkeys, checklist |
| [statistics-and-bayes.md](topics/statistics-and-bayes.md) | Beta posterior of win rate, Bayes factor and required trade count, PSR / DSR math, multiple testing, effective sample size, years to significance |
| [combining-edges.md](topics/combining-edges.md) | Carver forecast framework (scaling, caps, FDM / IDM, handcrafting), HRP, combining by daily correlation, meta-labelling, Kelly per strategy |
| [backtest-frameworks.md](topics/backtest-frameworks.md) | Lessons from HftBacktest, VectorBT, NautilusTrader, prediction-market backtesting; the four kinds of Monte Carlo |
| [markets-and-regimes.md](topics/markets-and-regimes.md) | Noise / efficiency ratio, which market suits which style, edge decay |
| [trend-following.md](topics/trend-following.md) | Why trends pay, methods compared, improvements (pullback, delay, filters) |
| [breakouts-and-opening-range.md](topics/breakouts-and-opening-range.md) | N-day and volatility breakouts, ORB family, inside-day filter |
| [mean-reversion-and-oscillators.md](topics/mean-reversion-and-oscillators.md) | RSI(2), oscillator timing, shock fades, gaps, pairs |
| [intraday-sessions-gaps-calendar.md](topics/intraday-sessions-gaps-calendar.md) | Time of day, gaps, weekday, month-end |
| [patterns-and-levels.md](topics/patterns-and-levels.md) | Chart/bar patterns with evidence, pivots, round numbers |
| [stops-exits-and-trade-management.md](topics/stops-exits-and-trade-management.md) | Stops, targets, scale out vs pyramiding, shock exits |
| [position-sizing-and-risk.md](topics/position-sizing-and-risk.md) | Sizing methods, vol targeting, risk of ruin, FTMO angle |
| [costs-and-execution.md](topics/costs-and-execution.md) | Spread, slippage, swap, gross vs net |
| [psychology-and-discipline.md](topics/psychology-and-discipline.md) | Probability mindset, execution rules |
| [volume-and-wyckoff.md](topics/volume-and-wyckoff.md) | Wyckoff laws, effort vs result, campaign cycle, VWAP; volume not in our data yet |

## Books read
| Short | Book | Notes | Character |
|---|---|---|---|
| K | Perry J. Kaufman, *Trading Systems and Methods*, 5th ed. (Wiley 2013) | [ch. 1-7](books/kaufman-tsm-ch1-7.md), [8-13](books/kaufman-tsm-ch8-13.md), [14-20](books/kaufman-tsm-ch14-20.md), [21-24](books/kaufman-tsm-ch21-24.md) | Reference work on systems and testing; most results gross of costs, 1990-2011 futures |
| D | Mark Douglas, *Trading in the Zone* (2000) | [notes](books/douglas-trading-in-the-zone.md) | Psychology; probability mindset, execution discipline; no tested rules |
| H | Tom Hougaard, *Best Loser Wins* (2022) | [notes](books/hougaard-best-loser-wins.md) | Psychology of an index day trader; pyramiding, no targets; claims unverified |
| V | Bob Volman, *Forex Price Action Scalping* (2011) | [part 1](books/volman-forex-scalping-part1.md) (setups), [part 2](books/volman-forex-scalping-part2.md) (exits, skips, sizing) | EURUSD 70-tick scalping, 20 EMA, 10-pip target; discretionary, no statistics |
| A | Andrew Aziz, *How to Day Trade for a Living* | [notes](books/aziz-how-to-day-trade.md) | US stock day-trading setups (ORB, VWAP, reversal, prev. close); discretionary, no statistics |
| C | Anna Coulling, *A Complete Guide to Volume Price Analysis* (2013) | [notes](books/coulling-volume-price-analysis.md) | Wyckoff-style volume reading; needs volume (not in histdata); no statistics |
| LP | Marcos López de Prado, *Advances in Financial Machine Learning* (Wiley 2018) | [ch. 1-11](books/lopezdeprado-afml-ch1-11.md), [12-22](books/lopezdeprado-afml-ch12-22.md) | Method book on false discoveries: triple barrier, meta-labelling, purging, CPCV, PBO, deflated Sharpe, strategy risk; theory and simulations, no strategy results; half of it needs tick / volume data |
| RC | Robert Carver, *Systematic Trading* (Harriman House 2015) | [notes](books/carver-systematic-trading.md) | Practitioner framework: continuous forecasts, vol targeting, cost speed limits; backtests after costs on 40+ futures, honest about low Sharpe (0.3-0.5 per instrument) |
| EC | Ernest P. Chan, *Algorithmic Trading* (Wiley 2013) | [notes](books/chan-algorithmic-trading.md) | Mean-reversion and momentum with statistical tests (ADF, Hurst, half-life), Kelly / CPPI; example Sharpes 1-2.4 are gross of costs and in-sample |
| KD | Kevin J. Davey, *Building Winning Algorithmic Trading Systems* (Wiley 2014) | [notes](books/davey-winning-algo-systems.md) | Practitioner pipeline of hard gates (limited test, walk-forward, monkeys, Monte Carlo, incubation); results net of costs but futures and one 4-year example |
| WK | Will Kurt, *Bayesian Statistics the Fun Way* (No Starch 2019) | [notes](books/kurt-bayesian-statistics.md) | Intro Bayesian statistics (Beta posterior, A/B test, Bayes factor); no trading content, methods translated to our win rates in the notes |
| JK | Jay Kaeppel, *The Option Trader's Guide to Probability, Volatility, and Timing* (Wiley 2002) | [notes](books/kaeppel-option-probability-volatility.md) | Options recipes with one showcase trade each, no statistics; only the volatility-rank and barrier-probability tools transfer. **The PDF is named "Option_Volatility_n_Pricing_-_Sheldon_Natenberg.pdf" but contains this book; Natenberg has not been read; the user decided 2026-10-16 not to add it.** |

Citation style in topics and ideas: `K p.950` (Kaufman book page), `D ch.11`, `H "Pressing Winners"`
(Douglas, Hougaard, Aziz and Coulling texts have no page numbers; Volman is cited by chapter),
`LP 3.6` (López de Prado chapter.section, ebook has no pages), `RC p.71` (Carver), `EC p.156` (Chan),
`KD p.109` (Davey), `WK ch.16` (Kurt, by chapter), `JK p.105` (Kaeppel).

## What the books say about our results so far
- **Strategy 4 (trend following) failing on indices is expected:** equity indices are the noisiest
  market and the worst for trend systems (K p.13-16, 1070); the best lookback shifts between periods
  (K p.225-227); results gross of costs look much better than net.
- **Unstable halves are the normal fate of a single optimised setting.** Kaufman judges by the share
  of profitable parameter combos (≥ 70 %), sibling markets and halves, never the best cell (K ch.21).
- **SMC tools (strategies 1-3) have no support in these books.** Kaufman and Hougaard both warn that
  pattern reading is mostly hindsight and that candlestick/Fibonacci claims fail mechanical tests.
- **The three practitioner books (V, A, C) are discretionary and give no statistics.** Their value is
  precise intraday rule ideas (compression breakouts, ORB with a range/ATR filter, session mean,
  previous-close magnet, exhaustion reversal) and exit/skip rules (tipping point, free path, never
  tighten a stop for the ratio). Volman's 10-pip brackets only work if spread ≤ ~10 % of the target.
- **Volume:** our histdata has none; volume ideas wait for MT5 tick volume (I-44).
- **Carver (RC): our expectations must be lower.** A realistic Sharpe is 0.3-0.5 per instrument and rule set and about 1.0 is the ceiling for a
  very diversified system; proving a true Sharpe of 0.3 at 2 sigma takes ~37 years, ranking two rules needs decades (RC p.71-73). Costs must stay
  under a third of the pre-cost Sharpe; day trading (500+ round trips) would need near-zero cost per trade, so retail day trading on CFD spreads is
  nearly impossible (RC p.192-205). Our 5 failed strategies fit this; the only cheap lever left is few trades and low cost.
- **López de Prado (LP): the problem is the trial count.** Every variant tried must be logged; the best of N null trials has a Sharpe growing
  ~sqrt(2 ln N), so "best of 24 variants" proves nothing unless deflated (DSR > 0.95). Walk-forward is one path; CPCV and PBO show the
  distribution. Meta-labelling only filters a primary signal that already exists, it does not create edge, and it needs the same purged tests
  (LP 3.7, 11.5-11.6, 12.4, 14.7).
- **Davey (KD): expect 100-200 ideas per tradable system.** Each stage is a hard gate set before testing (≥ 70 % of the grid profitable, entry beats
  ≥ 90 % of matched random "monkeys", walk-forward, Monte Carlo, 3-6 months incubation); failed ideas are scrapped, not patched. 9 of 10 ideas on
  1-5 minute bars fail; moving to 60 minutes nearly always helps (KD p.88, 105-114).
- **Chan (EC): measure before building rules.** ADF / Hurst / half-life / variance ratio use every bar and say whether a horizon mean-reverts or
  trends (EC p.41-48, 134-137). His gap momentum (open beyond the previous high / low by 0.1 daily sd, exit at the close, Eurostoxx Sharpe 1.4 gross)
  is the **opposite** of our failed gap fade (strategy 5) and a cheap test (EC p.155-157). Expect live Sharpe at best half of the backtest.
- **Kurt (WK): small samples cannot show small edges.** With a skeptical prior (we have 0 working strategies in 5), proving 55 % vs 50 % wins needs
  ~1,400 trades and 52 % vs 50 % ~8,600; a Beta posterior of the win rate plus a Bayes factor says this in numbers (WK ch.16-17, notes M4).
- **Kaeppel (JK): little transfers.** Volatility rank (decile of the instrument's own history) as a regime label and the random-walk barrier odds
  (P(target before stop) = S/(S+T)) are the usable parts; the book gives no statistics (JK p.69-72, 91-95).
- **Swap pushes us toward day trades** (ORB, shock fade, time-of-day, midday rules) or short holds
  (RSI(2)), which also suit the noisy indices.

## Adding a new book (process)
1. User puts the PDF into `00_Literature/Trading` and says which book.
2. Claude extracts the text (`pdftotext -layout`) into the scratchpad, finds the chapter lines and
   splits big books into parts of about 10-15 k lines.
3. One Sonnet agent per part with [reading-brief.md](reading-brief.md) (update the project context in it
   first). Each writes notes in the fixed format: overview, chapter notes, topic tags, testable ideas,
   warnings.
4. Claude reads the notes, copies them to `books/<author>-<short-title>.md` (with the header line),
   adds the book to the table above, merges new points into the `topics/` files (with source refs) and
   new ideas into `ideas.md` (next free ID; merge duplicates into existing ideas, add the new source).
   New subjects get a new topic file and a row in the topics table.
5. Commit only `knowledge/` ("Add <book> to knowledge base").

Rules: own words only, no long quotes (copyright); keep page/chapter refs; mark claims without
evidence as claims; note whether results are gross or net of costs.
