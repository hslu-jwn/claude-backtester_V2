# Brief: forward book report (FBK; reporting only, no orders)

Worker: Claude Sonnet subagent. Coordinator: Opus. Read first: `AGENTS.md`; `docs/research-runner.md` › M10, M13 and
the "Forward book" bullet; `research/screens/2026-11-17_shelf_forward.py` (`status`, the shelf rows and their units);
`src/backtester/tools/crypto_carry.py` / `crypto_flow.py` (Strategy 19 / 20 forward logs, `forward_path`);
`research/ledger.csv` and the cards in `knowledge/ideas.md` for each member's registered numbers.

## Design (decided by Opus 2026-11-27; implement as written)
- **Members:** every shelf row that is tradable: shelf_i100, shelf_i84, shelf_i98, shelf_h11, shelf_i71, shelf_i143,
  shelf_i109_ief (not shelf_i109, the statistic; not shelf_i105, report only since 2026-11-26), plus Strategy 19's and
  Strategy 20's main (Monday, not liquid) forward logs. Later POOLED-POSITIVE rows are added by one line in a
  `MEMBERS` table.
- **Registered inputs per member (a constant table in the script, each entry with a comment naming its source row /
  card line):** unit (bp or R), periods per week at registration (e.g. 1 weekly, 5 daily, ~0.23 month-end, events: dev
  events / dev weeks), registered net mean per period, registered sd per period, verdict class and its M10 factor
  (0.65 PASSED, 0.4 UNPROVEN-POSITIVE / POOLED-POSITIVE). Never use forward data to size.
- **Weekly unit:** each member's net per period is summed into ISO weeks (Monday 00:00 UTC start, by the period's
  date) and divided by its registered weekly sd (sd_period x sqrt(periods per week)); a week without a period is 0.
- **Weights:** w_i proportional to the shrunk weekly Sharpe (M10 factor x mean_week / sd_week), normalised to sum 1;
  members with a non-positive shrunk Sharpe get 0. Correlations assumed 0 (stated in the output).
- **Report:** per member: periods logged, forward mean (own unit), forward z, shrunk expectation, weight; book: weeks,
  weekly mean and sd in risk units, z, expected z at the shrunk mean, cumulative. Missing log file = "no rows yet".

## Build
- `research/screens/2026-11-27_forward_book.py` with `report` (prints the above) and `--selfcheck` optional.
- `tests/tools/test_forward_book.py` (hand-built logs in `tmp_path`): week bucketing (a Sunday period goes to the week
  started the Monday before; UTC), weekly sd scaling, zero-weight for non-positive shrunk Sharpe, weights sum 1, empty /
  missing logs, R and bp members combine only in risk units, no forward data used for weights (changing forward rows
  leaves the weights unchanged).

## Allowed / forbidden
- May create only those two files. Read-only on everything else. No commits / pushes / branches; no servers or lasting
  processes; no credentials; never edit `src/backtester/live/`, `.env`, `src/backtester/tools/notify.py`; no
  downloads; no package installs. `ruff check` + `ruff format` on your files; run your tests; run `report` once (today
  every log is missing, so it prints "no rows yet" lines and the weights).

## Done =
Tests green, ruff clean, `report` output pasted, the input table with sources, every assumption, open questions.
