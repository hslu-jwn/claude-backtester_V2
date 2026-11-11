# B-risk implementation handoff (V2.4)

B1-B3 implement the final decisions in `README.md` B (rule set by the user, 2026-10-22).
Strategy trades and strategy code are unchanged. No commit, push, branch creation, protected
live-code edit, or credential access was performed. Independent review and user acceptance
remain with the dispatcher/user; this is an implementation report, not approval.

## B1: daily-loss money

- Changed `src/backtester/risk/prop_rules.py` and `src/backtester/ui/live_model.py`:
  compare day-start balance minus equity with the daily-loss percentage of initial balance.
  The personal daily stop retains its day-start base.
- `risk/monte_carlo.py` already used initial-balance daily limits; regression cases protect
  both its fixed and adaptive paths above and below the initial balance, at and below the limit.
- Specs: `docs/risk-management.md`, `docs/live-trading.md`, with the required decision date.
- Tests: 11 new B1 cases in `tests/risk/test_review_b_risk.py`, covering monetary boundaries,
  custom percentage/initial override, both replay paths and Live display/missing data.
- Existing expected values changed: **none**. In `tests/ui/test_live_model.py`,
  `test_ftmo_bars` and `test_ftmo_bars_gain_and_breach_and_missing` now supply monetary
  `day_pl` fixtures. Their expected bar values remain unchanged; the first fixture's
  day-start percentage is made consistent with its balance and monetary P/L.

## B2: full passing days and unfinished attempts

- Changed `src/backtester/risk/monte_carlo.py`: both paths complete a passing day and
  test its closing balance; a later breach overrides an earlier target. Count unfinished
  attempts in either phase without inventing another attempt after the last trading day.
- `attempts` keeps its finished-only meaning. Added `unfinished_attempts`, `total_attempts`,
  `unfinished_share`; pass probability remains passes / finished attempts. The unfinished
  share uses all attempts. Failure shares in the UI/HTML use all attempts as the spec requires.
- Changed `src/backtester/risk/prop_card.py` (card version 4 invalidates old caches),
  `src/backtester/ui/prop_firm_card.py`, `src/backtester/tools/monte_carlo.py`, and
  `src/backtester/tools/risk_sweep.py`: carry/report unfinished count and share, including
  fixed/adaptive card columns, full-report HTML and sweep JSON/CSV/Markdown.
- Spec: `docs/risk-management.md`, with the required decision date.
- Tests: 13 new B2 cases in `tests/risk/test_review_b_risk.py` and two in
  `tests/tools/test_review_b_reports.py`. They cover late breach/lost target, day-end balance,
  mixed pass/fail/unfinished counts, unfinished phase 2, empty input, no phantom attempt,
  both risk paths, card rendering and exported reports.
- Existing expectations changed: `tests/risk/test_adaptive_risk.py`'s
  `test_fixed_risk_numbers_are_bit_identical_to_before` is renamed
  `test_fixed_risk_regression_with_full_passing_days`. Its three FTMO golden tuples change
  because later trades on passing days now run. Account-path final balances and drawdown
  expectations remain exactly unchanged. Tuple fields below are finished attempts, passes,
  daily failures, max failures, median days to pass, funded observed, funded loss probability.

| Risk | Before | After |
|---|---|---|
| 0.5% | `(38, 38, 0, 0, 73, 27, 0)` | `(35, 35, 0, 0, 74, 26, 0)` |
| 1% | `(64, 63, 0, 1, 40, 43, 20/43)` | `(62, 60, 0, 2, 42, 41, 18/41)` |
| 1.5% | `(126, 106, 0, 20, 26, 90, 88/90)` | `(124, 101, 1, 22, 29, 85, 83/85)` |

## B3: entry-known adaptive risk

- Changed `src/backtester/risk/monte_carlo.py`: reserve each accepted open trade's initial
  risk money, fixed at entry. Neither budgeting nor the open-risk breach approximation uses
  future R. Actual losses beyond the initial stop count when that trade exits.
- Spec: `docs/risk-management.md`, with the required decision date and weighted-trade handling.
- Tests: six new B3 cases in `tests/risk/test_review_b_risk.py`: challenge/funded risk bases
  and weights 0.5/1/2, each replayed with an open trade's future result changed from +1R to
  -1.5R and -20R. The next trade's sizing/skips are identical; oversized realised losses still breach.
- Existing expectation changed: `test_open_trade_counts_at_realised_loss_beyond_one_r`
  in `tests/risk/test_adaptive_risk.py` is renamed
  `test_open_trade_counts_at_initial_risk_even_if_it_later_loses_more`. At a 2.25% budget,
  trade 1 receives 1,000 rather than 750, so expected closing balance changes **99,250 -> 99,500**.
  Its 2.5% budget expectation remains 99,500.

## Validation and remaining handoff

- Tests were written and observed failing before the corresponding production changes.
  The first daily-breach fixture was corrected from -6R to -15R: after a +10R gain,
  -6R still leaves a day profit; -15R correctly breaches. The expected breach was retained.
- Focused checks: 235 risk/Live/card tests passed; 47 report/sweep tests passed.
- Final full suite: **3,540 passed, 5 skipped, 1 xfailed**, 44 dependency/deprecation
  warnings, in 201.26 seconds. `ruff check .` and `git diff --check` are clean.
- Full-suite output: `results/b-risk-full-suite.log`; lint output: `results/b-risk-ruff.log`.
  Initial failing runs: `results/b-risk-red.log`, `results/b-risk-reports-red.log`.
- No trading-rule questions remain. Strategy trade goldens were not rewritten because no
  strategy trade generation changed. The existing overnight-trade approximation remains
  documented in `docs/risk-management.md`.
- No live behavior changes remain: `src/backtester/live/bot.py:775-777` already calls the
  shared guard with initial balance; `src/backtester/live/status.py:187,190` already publishes
  day-loss money and initial balance. The comment at `src/backtester/live/bot.py:354` still
  describes initial balance only as the max-loss base; the dispatcher may update it to say
  both FTMO loss limits. It was left untouched under the protected-path rule.
