# Brief: V2.7 groundwork, goal-2 portfolio screen (analysis only)

Write ONE new script `research/screens/2026-11-19_v27_goal2_portfolio.py` (no other file changes, no
`src/` edits, no tests needed beyond the self-check below). Report only; it decides nothing.

## Inputs (reuse the existing code, do not re-implement the strategies)

1. Strategy 20 crypto taker-flow sort: weekly net returns (bp) from `backtester.tools.crypto_flow`
   (`load`, `compute_weeks` / `anchored_weeks`; spec `docs/strategy-crypto_flow.md`), the frozen default variant.
2. Strategy 19 crypto carry: weekly net returns (bp) from `backtester.tools.crypto_carry` (spec
   `docs/strategy-crypto_carry.md`), frozen default.
3. I-109 Treasury month-end: monthly net returns (bp) as computed in
   `research/screens/2026-11-17_i109_treasury_month_end_screen.py` (DGS10 duration proxy, development
   and IEF test); import its functions via importlib like `2026-11-17_shelf_forward.py` does (`_load`).

Use cached data only (no downloads); if a cache is missing, print which and skip that stream.

## Output (stdout, plain text)

- Per stream: period, n, mean, sd, t, annualised Sharpe (weekly x sqrt(52); monthly x sqrt(12)).
- Aligned on calendar months (sum weekly bp inside a month): pairwise correlation of monthly returns
  over the overlapping months, with n.
- Equal-risk combination (each stream scaled to the same monthly sd over the overlap): mean, sd,
  Sharpe, max drawdown (in units of one stream's monthly sd), and the same with each stream left out.
- Split by the project's periods: crypto develop 2020-2023 / test 2024+; I-109 development before
  2021-09-14 / test after. Label every number with its period; never mix them silently.
- Self-check: assert the combination of a stream with itself gives correlation 1.0 and that the
  equal-risk weights sum to the number of streams.

## Rules

No lookahead (monthly bucket by return date). Read-only on data. Ruff clean
(`.venv/Scripts/python -m ruff check research/screens/2026-11-19_v27_goal2_portfolio.py`). Run the
script once and paste its output at the end of your answer. Never commit.
