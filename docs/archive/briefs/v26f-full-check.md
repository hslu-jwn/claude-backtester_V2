# Brief: V2.6 step 8 — full check, review of the V2.6 / V2.7 code (read-only)

Context: ROADMAP › V2.6 build order step 8. The 2026-10-23 review (`docs/review/`) covered the 8
modules then; everything below was added since (2026-10-26 / 27) and was only reviewed piece by
piece. **Read-only task: change no file.** Write your findings as your answer (Opus saves them to
`docs/review/v26-full-check.md`).

## Scope (new code)

- `src/backtester/jobs/`, `src/backtester/filelock.py`, `tools/queue.py` (job queue)
- `data/cache_repair.py`, `tools/cache_repair.py`, `data/histdata.py` (clock table, invalid
  periods, continuity check), `data/mt5_download.py` changes
- `tools/research_pipeline.py`, `tools/lanes.py`, `ui/queue_panel.py`, `ui/queue_model.py`
- `analytics/portfolio_search.py`, `tools/portfolio_candidates.py`, `tools/portfolio.py`
  (`--existing`, `--test`), `ui/pages/portfolio.py`
- `ui/review.py`, `ui/review_callbacks.py`, `ui/trade_focus.py`, `ui/parameter_heatmap.py`,
  `ui/strong_move.py`, chart changes in `ui/pages/chart.py` / `assets/chart.js`
- `data/news.py`, `tools/news_diagnostics.py`, the news parts of `engine/backtest.py` and
  `tools/research.py`
- `engine/costs.py` default spread table + tick rounding (`default_spread_table`)

## What to look for (in this order)

1. **No look-ahead / test-period leaks:** anything that lets future data, results after the
   decision time, or test-period (from 2021-09-14) data reach a strategy, a development-period
   result, the review mode before reveal, or the portfolio search.
2. **Correctness bugs** with a concrete failing scenario (inputs -> wrong output / crash), incl.
   Windows specifics (file locks, `os.replace`, process trees, paths relative to the working folder).
3. **Data integrity:** anything in the cache repair / import that could silently drop, shift or
   duplicate days, or write a half file.
4. **Concurrency:** queue runner vs CLI vs UI writing the same files.
5. Then: dead code / duplication between the new modules (short list only).

## Answer format

Ranked findings, most severe first, each: file:line, one-sentence defect, concrete scenario,
suggested fix (one line), and whether it touches a trading rule / default (then Opus only lists
it for the user). Then "checked, looks fine" in a few lines. Max ~1500 words. No trading-rule
guesses; report unclear rules.
