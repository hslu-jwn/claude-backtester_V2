# Brief: V2.6 build step 4 — V2.7 Portfolio page

Context: ROADMAP › V2.7 and › V2.5-V2.7 in detail › V2.7 Portfolio (main goal: combine
strategies that balance each other by regime for a smoother equity curve and a higher prop-firm
pass probability; the user picks). Existing: `analytics/portfolio.py` (daily R, correlation,
rolling correlation, IDM, equal weights, combine), `tools/portfolio.py` (components file ->
backtest each -> equal-weight merge -> Monte Carlo report), `analytics/regime.py` +
`docs/regime-classifier.md`, research cards (`ui/research_model.py`), the queue + pipeline
(`docs/research-runner.md` › Job queue, Pipeline). Decisions of the user, 2026-10-26, below.
No trading rule or default changes.

## Decisions of the user (2026-10-26)

1. **Development period only** for choosing combinations (data before 2021-09-14, the same
   rule as strategies). The chosen portfolio gets **one** test on the MT5 test period later,
   **CLI only**, recorded in the trial log and refused a second time for the same member set.
   Nothing in the app may compute or show test-period results for a candidate.
2. **Equal weights** only (as `tools/portfolio.py`: never optimised).
3. **New top-nav tab "Portfolio"** next to Research.
4. **Search 2-4 members** from a pool the user picks; rank every set by cheap daily-R
   metrics; Monte Carlo + prop-firm pass probability only for the **top 10**, through the
   queue.

## What to build

A. **Members** = the chosen variants of research grids (the research cards): their
   development-run trade lists and daily R series already exist (`daily.csv` per variant,
   V2.4d; dev run folders). **Reuse them; never re-backtest a member** for the search. A
   member must be a development-only result; refuse anything else.
B. **Search** (`analytics/portfolio_search.py`, plain Python, no Dash): for every set of 2-4
   members of the pool, equal-weight combined daily R over the common development days ->
   net R, max drawdown (R), net R / max DD, Sharpe of daily R (annualised), worst month, longest
   drawdown (days), average pairwise correlation of daily R, IDM; per regime
   (`analytics/regime.py`, the members' symbols' regime per day as the classifier defines it;
   if a set spans symbols, document the rule you use and ask in the report if unclear) net R and
   R / day; **leave-one-out**: the same cheap metrics for the set minus each member. Pool size
   limit 12 (C(12,2..4) = 781 sets); fast (vectorised; target < 30 s for 12 members).
   No pass / fail verdicts: sortable numbers; the user decides.
C. **Monte Carlo for the top 10** (sort key chosen in the UI, default net R / max DD): one
   queue job per set running the existing Monte Carlo / prop-firm machinery on the merged
   member trade lists (reuse `tools/portfolio.py` / `tools/monte_carlo.py` functions; extend
   `tools/portfolio.py` to accept existing trade lists instead of re-backtesting), development
   period only; results in `results/portfolio/<set-id>/` (`summary.json` + report) where the page
   reads them. Prop-firm pass probability and typical time to pass as in the strategy cards.
D. **One-time test (CLI only):** `python -m backtester.tools.portfolio --test <set-id>`: runs
   the set once on the MT5 test period (from 2021-09-14), writes the trial log, refuses a second
   run for the same member set (sorted member ids) with a clear message. No UI path.
E. **Portfolio tab** (`ui/pages/portfolio.py`, V2.5 look: `ui/layout.py`, tokens, `info()`):
   pool picker (cards' chosen variants with strategy, symbols, net R, flags), "Find
   combinations" -> sortable table of sets (members, metrics above, average correlation);
   "Monte Carlo top 10" queues the jobs (queue panel shows them); click a set -> details:
   combined equity curve (development), correlation matrix of daily R, regime breakdown, leave-
   one-out table, Monte Carlo / pass probability when done. Search results cached in
   `results/portfolio/search_<pool-hash>.json`.

## Answers given up front (Opus, 2026-10-26)

- Common days: a set's combined series covers the days all members have data; report how many
  days were dropped. A member with fewer than 250 common days -> the set is listed with a
  warning flag, not removed.
- Annualise with 252 trading days. Correlation: Pearson on daily R, days where both are 0 kept.
- Set id: sorted member ids joined and hashed (stable).
- Never call `--retest` / any test-period run from the app or the search.

## Rules

AGENTS.md (no commit / push / branch; no lingering processes; never `src/backtester/live/`; no
credentials; never start the app). Test-case list first (`briefs/v27-test-cases.md`), then tests
(`tests/analytics/test_portfolio_search.py`, `tests/tools/`, `tests/ui/test_portfolio_page.py`),
then code; hand-built series where the answer is obvious (two perfectly anti-correlated members
-> flat combined curve; leave-one-out of a 2-set equals the single member). Run only your tests
(`pytest -q tests/analytics tests/tools/test_portfolio*.py tests/ui > results\pytest_v27.log 2>&1`)
+ ruff on touched files. Docs: `docs/portfolio.md` (new: what the tab computes, the test rule).
Report: files changed, test results, the regime rule for multi-symbol sets, open questions.
