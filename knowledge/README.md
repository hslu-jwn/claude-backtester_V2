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
| [testing-and-robustness.md](topics/testing-and-robustness.md) | IS/OOS, walk-forward, parameter plateaus, robustness %, shocks, checklist |
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

## Books read
| Short | Book | Notes | Character |
|---|---|---|---|
| K | Perry J. Kaufman, *Trading Systems and Methods*, 5th ed. (Wiley 2013) | [ch. 1-7](books/kaufman-tsm-ch1-7.md), [8-13](books/kaufman-tsm-ch8-13.md), [14-20](books/kaufman-tsm-ch14-20.md), [21-24](books/kaufman-tsm-ch21-24.md) | Reference work on systems and testing; most results gross of costs, 1990-2011 futures |
| D | Mark Douglas, *Trading in the Zone* (2000) | [notes](books/douglas-trading-in-the-zone.md) | Psychology; probability mindset, execution discipline; no tested rules |
| H | Tom Hougaard, *Best Loser Wins* (2022) | [notes](books/hougaard-best-loser-wins.md) | Psychology of an index day trader; pyramiding, no targets; claims unverified |

Citation style in topics and ideas: `K p.950` (Kaufman book page), `D ch.11`, `H "Pressing Winners"`
(Douglas and Hougaard texts have no page numbers).

## What the books say about our results so far
- **Strategy 4 (trend following) failing on indices is expected:** equity indices are the noisiest
  market and the worst for trend systems (K p.13-16, 1070); the best lookback shifts between periods
  (K p.225-227); results gross of costs look much better than net.
- **Unstable halves are the normal fate of a single optimised setting.** Kaufman judges by the share
  of profitable parameter combos (≥ 70 %), sibling markets and halves, never the best cell (K ch.21).
- **SMC tools (strategies 1-3) have no support in these books.** Kaufman and Hougaard both warn that
  pattern reading is mostly hindsight and that candlestick/Fibonacci claims fail mechanical tests.
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
