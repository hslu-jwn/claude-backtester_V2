# Brief: design multi-symbol strategy support (read-only design, no code changes)

Read `AGENTS.md` first (no lookahead invariant, `SeriesView`, R-based trades, layers); hard limits apply (no
commits, no servers, no `live/`, no `.env`). Read-only: write only the design file below.

## Why

Strategies today see one symbol (`strategy/base.py`, `engine/backtest.py`, `runner.py`). Many researched ideas
need other symbols: (a) a signal from symbol B traded on A (oil -> index, BTC weekend -> gold, USD breadth -> a
pair); (b) two-leg spreads (WTI-Brent, gold-silver ratio, EURGBP dislocation); (c) cross-sectional baskets
(FX relative strength rank, commodity sorts). See `research/candidates/README.md` (multi-symbol rows) and
`knowledge/research/reports/2026-11-10_idea_harvest_practitioner.md` ideas 1-5, 12.

## Deliver `docs/design/multi-symbol.md`

1. How data, replay (time alignment of several M1 series, missing candles, different sessions / DST) and
   the no-lookahead guarantee would work for several symbols (one shared clock; each strategy sees closed
   candles of every symbol up to `now`).
2. Smallest step that unlocks (a) signal-from-B-trade-A: e.g. read-only `SeriesView`s of extra symbols handed
   to a single-symbol strategy, trades still per symbol. Then (b) two-leg trades and their R definition,
   costs, swap and risk (`risk/`), and (c) baskets. Rank by value / effort.
3. What changes in runner, research runner (grids, data split, gates tools), golden lists, UI (can stay
   single-symbol at first), and tests (a no-lookahead test across symbols).
4. Effort estimate per step and the files touched. Flag anything that would change existing results (must
   be none: existing strategies stay bit-identical).
Report the file and a 5-line summary.
