# Brief: challenge path simulator, increment 1 (core + CLI, no UI)

You work in a lane worktree of the V2 repo. Read `AGENTS.md` first (hard limits: no commits, no
branches, no servers, no credentials, never edit `src/backtester/live/` or `.env`).

## Spec

`docs/risk-management.md` › "Challenge path simulator and FTMO rule sets" (read all of it; it is the
source of truth, including the rule-set table and "Rules of the simulator"). Reuse
`risk/monte_carlo.py`: `build_days`, `Day`, the worst-point equity approximation of `_play_day` and
`EPS`. Do NOT change `monte_carlo.py` behaviour (its tests and outputs must stay identical); if you
need a shared helper, add it without changing existing results.

## Files you may create / change

- new `src/backtester/risk/challenge_path.py`
- new `src/backtester/tools/challenge_path.py` (CLI)
- new `tests/risk/test_challenge_path.py`, new `tests/tools/test_challenge_path_tool.py`
- `tests/test_layers.py` only if the layer test needs the new tool classified (follow how
  `tools/monte_carlo.py` is classified)

## What to build

1. `RuleSet` frozen dataclass: `name`, `targets: tuple[float, ...]` (empty = Instant), `daily_loss`,
   `max_loss`, `max_loss_mode` in {"static", "eod_trailing", "intraday_trailing"}, `min_trading_days`,
   `consistency: float | None`, `risk_base` in {"balance", "initial"}. Validation in `__post_init__`.
   `RULE_SETS = {"ftmo_2step": ..., "ftmo_1step": ..., "ftmo_instant": ...}` exactly per the spec table.
2. `play_attempt(days, start_index, rules, risk, initial=100_000.0, watch_days=126) -> Attempt`:
   plays from `days[start_index]`. `Attempt` (frozen dataclass, JSON-able via a `to_dict()`): `status`
   ("pass" | "daily" | "max" | "open" | "survived" for Instant), `start_index`, `end_index`,
   `weekdays_to_end`, `phase_results` (per phase: status, days), `payout_day` (Instant, else None),
   and a path list per weekday: `{"day": index, "balance": closing balance, "worst": worst equity of
   the day, "daily_floor": day_start - daily_loss*initial, "max_floor": the max-loss floor in force}`.
3. `simulate(trades, start, end, rules_names, risk, fees=None, watch_days=126) -> dict`: attempts from
   the first weekday of every month in start..end; per rule set the summary of the spec (attempts,
   pass %, breach % daily / max, open, median and p90 weekdays to funding, cost per funded account
   when a fee is given; 2-Step reported "before refund" and "after refund" = 0 cost when passed).
   Deterministic; no randomness.
4. CLI `python -m backtester.tools.challenge_path <run id> [--risk 0.01] [--rules ...] [--fee name=price ...]
   [--watch-days 126] [--results-dir results]`: loads the run like `tools/monte_carlo.load_run`
   (reuse it), writes `results/<run id>/challenge_path.json` (summary + every attempt with its path) and
   a short `challenge_path.md` (summary table per rule set, the not-modelled rules: news / market-break
   restrictions on funded and Instant accounts, fees not published). Bad input -> argparse error, no traceback.

## Test cases (write them first; hand-built trades with obvious answers)

- 2-Step: +2 R per day at 1 % risk passes phase 1 on the day the balance reaches 110,000 but only once
  4 trading days are done; Verification starts the next day at 100,000 and needs 5 % and 4 days.
- Daily loss 2-Step: a day whose worst point is exactly 5,000 below the day start is a breach ("daily"),
  4,999 is not. 1-Step / Instant: same at 3,000.
- Static max loss: balance 90,000 + EPS breach ("max"); daily checked before max on the same event.
- 1-Step end-of-day trailing: balance rises to 108,000 at a day end -> next day floor 98,000; an
  intraday high of closed balance 109,000 that closes the day at 107,000 does NOT raise the floor above
  98,000 (end-of-day only); the floor never falls after losses.
- Instant intraday trailing: floor rises at the moment a trade closes at a new closed-balance high
  (109,000 -> floor 99,000 immediately, within the same day); risk is a share of the initial balance.
- 1-Step consistency: target reached with one day holding 60 % of the profit -> not passed, attempt
  continues; it passes on the first later day end where best day <= 50 % of the total phase profit.
- Instant: no target; "survived" after `watch_days` weekdays without breach; `payout_day` = first day end
  with balance > initial and best day <= 30 % of total profit.
- Open attempt: data ends before pass / breach -> "open", not counted in pass % or breach %.
- Monthly starts: a run 2020-01-01..2020-03-31 gives 3 attempts per rule set starting on the first weekday
  of each month; an attempt never uses a trade exiting before its start.
- Determinism: two calls give identical dicts. Fees: cost per funded = fee / pass rate; pass rate 0 ->
  None (not infinity).
- CLI: writes both files into a tmp results dir from a hand-made run folder; unknown rule name -> exit 2.

## Done =

All new tests pass, `python -m pytest -q -p no:cacheprovider -n 8` green, `python -m ruff check .`
clean. Report: files changed, test results, every rule question you hit with your answer.
