# Reading brief for book agents

Give this file to each reading agent (Sonnet is enough). Replace the project context if it is outdated
(check `docs/HANDOFF.md` and CLAUDE.md › Status). The agent writes one notes file to the scratchpad;
Claude then copies it to `books/` and merges it into `topics/` and `ideas.md`.


You are reading part of a trading book to build a knowledge base for a Python backtester project.
Write ONLY your notes file (path given in your task). Do not touch any repo files. Do not run git.

## Project context (updated 2026-11-18)
- Python backtester and research platform. Data: FTMO MT5 M1 candles for ~34 CFDs (FX, gold, indices, oil), daily
  bars of ~23,700 US shares (Alpaca, 2015+), Binance crypto perpetuals (prices, funding, taker flow), FRED Treasury
  yields, Cboe VIX futures, EIA energy futures contracts 1-4, Yahoo continuous 10-year Treasury futures, free CFTC
  COT positions. No order book, no paid per-contract futures history. Costs (spread, commission, swap, fees) modeled.
- Venues: FTMO prop CFDs (goal 1), exchange futures, real US shares, crypto perps (goal 2).
- Results so far: almost every price-pattern, trend, breakout, gap and intraday idea on CFDs died on costs (the "cost
  wall"). Two streams passed a one-time test: a weekly crypto taker-flow long-short sort (Strategy 20) and the
  Treasury month-end duration extension (long 10-year bonds the last 3 days of a month, index funds must buy).
- Method rules in use: pre-registered gates, a power check before any data look, one-time test per idea, t >= 3.0
  on development, multiple-testing ledger, three verdicts (falsified / unproven-positive / passed), shrunk forecasts.
- Focus now: edges from a counterparty that MUST trade (index rebalancing, rolls, hedging, ETF flows, funding,
  dealer inventory), and honest testing (causality, multiple testing, power, small samples, fat tails).
- So we look for: testable mechanism-based ideas on the data above, and methods that make tests more honest.

## How to read
- Text was extracted with pdftotext into a .txt file. Read it with the Read tool in chunks
  (offset/limit, ~1500-2000 lines each). Cover your whole assigned range. Skim formula listings,
  code listings and long tables; read prose carefully.
- Copyright: write everything in your OWN words. No passages copied. At most a handful of very short
  quoted phrases (under 15 words) for key terms. Give chapter/section names and book page numbers
  (page numbers appear in the text as headers/footers) so we can look things up again.

## Notes file format (Markdown)
1. `## Overview` - what this part covers, 5-10 lines, overall stance of the author.
2. `## Chapter notes` - per chapter: `### Ch N - Title (pp. x-y)` with 5-20 bullets of the key ideas,
   methods, rules, parameter defaults, and the author's own test results/claims (with numbers if given).
3. `## Topic tags` - for each of these topics, bullets of what this part says (skip empty ones):
   trend, breakout, mean-reversion, momentum/oscillators, patterns, intraday/sessions, seasonality/time,
   volatility, stops-and-exits, position-sizing/risk, testing-and-robustness/overfitting,
   costs/execution, psychology/discipline, portfolio/diversification.
4. `## Testable ideas` - every idea that could become a backtest on OUR data. For each:
   **Name** - rule in 2-4 precise lines (entry, exit, stop, timeframe, parameters with the author's
   defaults) - source (chapter/page) - author's claimed evidence - fit for our data/costs (good/poor and
   why; note swap if it holds overnight) - how it differs from the 4 failed strategies.
   Mark the 3-5 most promising with ★.
5. `## Warnings / pitfalls` - what the author says goes wrong (overfitting, costs, regime change, ...).
Be thorough but dense. Aim for 1500-4000 words depending on the size of your part.
