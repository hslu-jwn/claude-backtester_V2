# Reading brief for book agents

Give this file to each reading agent (Sonnet is enough). Replace the project context if it is outdated
(check `docs/HANDOFF.md` and CLAUDE.md › Status). The agent writes one notes file to the scratchpad;
Claude then copies it to `books/` and merges it into `topics/` and `ideas.md`.


You are reading part of a trading book to build a knowledge base for a Python backtester project.
Write ONLY your notes file (path given in your task). Do not touch any repo files. Do not run git.

## Project context
- Backtester replays historical M1 candles (histdata.com) for XAUUSD, GBPUSD, GBPJPY (FX/gold) and
  NAS100, US500 (indices), years 2018/2020-2026. Can resample to any timeframe (1m..1d). No volume (histdata volume column is always 0; MT5 tick volume only later),
  no open interest, no order book, no futures term structure, no options data. Spread + commission +
  swap (overnight financing) costs are modeled. Trades are simulated in R multiples (risk units).
- Target: pass / trade FTMO prop-firm accounts (max daily loss 5%, max total loss 10%, profit targets).
- Strategies already tested and FAILED (net negative or not robust): (1) session-zone liquidity sweep
  (SMC style: FVG, order block, BOS) on FX/gold; (2) NY-open index sweep on NAS100/US500; (3) no-wick
  candle with the trend; (4) Kaufman trend following (N-day breakout, SMA + ATR band, momentum, KAMA,
  Dunnigan) 15m-1d with 3xATR stop and stop-and-reverse: swap costs kill holding periods, edge not
  stable across halves of the sample.
- So we look for: fundamentals, robust testing methods, risk/position-sizing knowledge, and NEW
  testable strategy ideas that fit our data (price only, intraday to daily, FX/gold/indices).

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
