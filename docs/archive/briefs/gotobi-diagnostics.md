# Brief: Gotobi G1 robustness diagnostics (hypothesis 11; not gates, nothing re-tuned)

Read `AGENTS.md` first; hard limits apply (no commits, no servers, no `live/`, no `.env`). Analysis only:
do not change strategy code, grids or the spec. Development data only. The frozen candidate is G1
(`research/grids/timed_hold_gotobi.toml`, gotobi, stop 1.0, USDJPY); its one-time test criteria are
fixed in `docs/strategy-timed-hold.md` › Hypothesis 11. These diagnostics can never replace or alter it.

## Inputs

Trades: `results/research/timed_hold_gotobi_d9ea62c1/variants/<id>/` (read with
`backtester.tools.timed_hold_gates.read_trades`; `variants.csv` maps family / settings to ids).

## Task

1. Split G1 gotobi stop 1.0 (USDJPY and EURJPY) by: target date (5, 10, 15, 20, 25, month-end), rolled-back
   vs on-date, weekday, Japanese fiscal quarter-end months (Mar, Jun, Sep, Dec) vs others, year. Per bucket:
   trades, net R, mean net R, win rate.
2. Entry/exit sensitivity in a separate scratch results folder (never overwrite the original run): run the
   research runner on a temporary copy of the grid written under `results/` (not `research/grids/`) with
   `--dev-only --results-dir <scratch>` for entry_time {01:00, 02:00, 04:00, 06:00, 08:00} and exit_time
   {09:30, 09:55, 10:30} (G1, gotobi and all, stop 1.0, USDJPY only). Report net R and the gotobi minus
   all-days difference per cell. If the runner cannot take a grid outside `research/grids/`, say so and skip.
3. Mean gross bp per trade (price move / entry price) for G1 gotobi vs all-days, USDJPY.

## Output

`knowledge/research/reports/2026-11-09_gotobi_diagnostics.md`: tables and 3-5 lines on whether the edge is
broad (many buckets positive) or concentrated (one bucket, one year). Report the file.
