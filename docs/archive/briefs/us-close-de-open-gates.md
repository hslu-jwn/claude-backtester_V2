# Brief: gates tool of strategy 14 `us_close_de_open`, test-first

Read `AGENTS.md` first; hard limits apply (no commits, no branches, no servers, no `live/`, no `.env`).
You work in the worktree `bt-lane-s14_gates`. You may create/change ONLY
`src/backtester/tools/us_close_de_open_gates.py` and `tests/tools/test_us_close_de_open_gates.py`.
Do not change any other file (reuse helpers by import). No backtest or research run. If a rule is unclear,
stop and report it with the spec line; never guess a trading rule.

## Sources (read them)

- Spec: `docs/strategy-us_close_de_open.md` › Cells, Control, Gates (1-7), multiple-testing paragraph,
  Assumption 5 (DST mismatch weeks) and the decisions G4, U1-U6 at the end.
- Pattern and helpers to import (do not copy): `src/backtester/tools/timed_hold_gates.py`
  (`variant_report`, `_p_value`, `_name`, `BEST_DATES`, `BLOCK`, `RESAMPLES`, `SEED`, the CLI reading
  `variants.csv` / `variants/<id>/settings.json` / `read_trades`), `src/backtester/tools/alternating_path_gates.py`
  (`net`, `STRESSES`, `block_indices`, `block_bootstrap`, `integrity_failures`), `tools/entry_screen.load_m1`.
  Tests to mirror: `tests/tools/test_timed_hold_gates.py`.

## Inputs

`python -m backtester.tools.us_close_de_open_gates <GER40 research folder> --breadth-folder <UK100 research folder> [--skip-integrity]`
writes `gates.json` into the GER40 folder and prints one line per cell. GER40 folder = grid
`research/grids/us_close_de_open.toml` (families S and C, 16 cells); UK100 folder = `us_close_de_open_uk.toml`.
A cell's settings come from the `set.*` columns plus `family` (S / C), as in timed_hold_gates.

## Per S cell (GER40 trades only), reported for all 8; only the primary cell can advance

Primary = family S, `min_ref_return_pct` 0.10, `stop_atr` 0.5, `exit_time` 09:30.

1. `positive_normal_and_doubled`: net R > 0 at normal costs and with every component doubled (`STRESSES`).
2. `positive_both_halves`: net R > 0 in both halves split at the **fixed** entry date 2017-10-08 (spec gate 2;
   trades entered before that UTC date in the first half), NOT the period midpoint.
3. `effect_not_drift`: matched control = the two C cells with the same `stop_atr` and `exit_time`
   (`direction` long and short). Remove from both the entry dates (Berlin date) of this S cell's trades.
   Statistic: mean net R of the S cell minus control mean, control mean = (n_long * mean(L) + n_short * mean(S_c))
   / (n_long + n_short), where n_long / n_short are the S cell's long / short trade counts and L / S_c the
   date-filtered long / short control series. Bootstrap: circular blocks of 5 trades, 10,000 resamples, seed
   2026110, each of the three series resampled independently (entry-time order), the weighted statistic per
   resample; gate passes if the 2.5 % quantile > 0. Report difference, lower_2_5, lower_5, n_long, n_short,
   control trade counts. Missing / ambiguous control cells -> gate False with a note.
4. `breadth`: UK100 folder, its primary cell (S, 0.10, 0.5, exit 08:30): UK100 net R > 0 at normal costs.
   Missing folder or cell -> False with a note. Report the UK100 primary report and all UK100 S cells' net R.
5. `best_date_removal_positive`: net R > 0 without the 5 best entry dates at normal **and** doubled costs (U5;
   `variant_report`'s `net_r_without_best_dates`).
6. `min_trades`: >= 200. Below 200: the cell's verdict is `not_enough_evidence` (G4), never falsified, never a pass.
7. `no_data_integrity_failure`: `integrity_failures(..., max_gap_minutes=5)` on GER40 M1 (more than 5 consecutive
   missing minutes in (entry, exit], missing exit candle, invalid candle). `--skip-integrity` -> gate False and
   `skipped_integrity: true` (unknown integrity never passes).
   Also report (not a gate): the number of signal days with a missing US500 signal candle: weekdays `D_s` in the
   period that are full NYSE sessions (`strategy/timed_hold/calendars/nyse_holidays.csv`, not closed, not
   early close) where the US500 M1 candle closing at 15:30 or at 16:00 New York is absent (US500 via the run's
   `cache_dirs`, `load_m1`). Skipped with `--skip-integrity`.

Also per S cell: `variant_report` numbers (incl. `by_direction`, `bootstrap`, `p_value`), `family_wise_level`
0.01 next to the raw p, and a DST-mismatch split (Assumption 5): trades whose entry time has New York on DST and Berlin
not, or the reverse (`bool(dt.astimezone(zone).dst())` differs between the two zones), vs the rest: trades and
net R each.

Verdict per S cell: `not_enough_evidence` if gate 6 fails; else `falsified` if mean net R <= 0, or the cell's own
`bootstrap` lower_2_5 <= 0, or gate 3 fails; else `advances` if it is the primary cell and all 7 gates pass;
else `rejected`. `advances` is only ever True for the primary cell. C cells: reported (`variant_report`),
verdict `control`, never advance.

## Tests first (`tests/tools/test_us_close_de_open_gates.py`), hand-built trade objects

Write them before the code. Cover: primary detection; fixed-date halves (a trade on 2017-10-07 vs 2017-10-08);
weighted control with an exact hand-computed difference (e.g. 3 long + 1 short signal trades; control means
known); control dates removed (overlapping date excluded); bootstrap determinism (same seed -> same numbers);
missing control cell -> gate False + note; breadth from a second folder (pass, fail, missing); gate 5 failing
only at doubled costs -> False; 199 trades -> `not_enough_evidence`; `--skip-integrity` -> integrity False; an
integrity failure via a gap > 5 minutes; non-primary cell never advances even if all gates pass; DST-mismatch
split counts (2019-03-12 in mismatch, 2019-04-02 not); CLI end-to-end on a tmp folder writes `gates.json`.

## Done =

`python -m pytest -q -p no:cacheprovider tests/tools/test_us_close_de_open_gates.py tests/tools/test_timed_hold_gates.py`
green and `python -m ruff check src tests` clean (run from the worktree with
`..\backtester-claude_V2\.venv\Scripts\python.exe`). Module docstring with the CLI and `Spec: strategy-us_close_de_open.md › Gates`.
Report: files, test results, any spec question.
