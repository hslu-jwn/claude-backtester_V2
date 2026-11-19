# Brief: share book factors screen (H1-H4)

Spec (source of truth, rules and gates): `docs/strategy-share_book_factors.md`. Read it fully first.

Write ONE script `research/screens/2026-11-19_share_book_factors_screen.py`, modelled on
`research/screens/2026-11-17_i101_short_volume_screen.py` (reuse its `closes` and `tstat` via importlib like
`2026-11-17_i104_attention_screen.py` does; copy its kill printout style). Steps:
`power` (shuffled-label control for H1 / H2, 200 draws) | `run` (development, all four cells) | `test` (one-time
test period for a cell named on the command line, e.g. `test H1`; refuse a cell that is not given).

Rules to get right:
- No lookahead: signals from closes strictly before the entry date; universe = the entry month's list.
- Month buckets: entry = first trade date of the month (trade dates = dates with an SPY close), exit = first trade date
  of the next month. Development = entries 2016-05-01 .. 2021-09-13; test = entries 2021-09-14 .. last complete month.
- H1 residual sd: OLS on SPY daily returns over the previous calendar month, >= 15 common days.
- H2 (entry month m): close on the last trade date of month m-2 over the close on the last trade date of month m-13
  (12-1 momentum, month m-1 skipped); >= 200 closes in that span.
- H3 / H4 exactly as the spec (event dates, 2 % of the 252-day low close, IWM-IWB).
- Print per cell: n, gross and net mean, t, sd, positive share, halves, doubled cost, without 2 best, kills hit and
  PASSED / KILLED; reported extras (deciles or quintiles, years, capped spread, beta to SPY).
- Self-check at import: a tiny hand-built frame where the quintile spread is known (assert).

Done = the script runs `power` and `run` on cached data without downloads, ruff clean
(`.venv/Scripts/python -m ruff check <file>`); paste both outputs at the end of your answer. Do NOT run `test`.
Change no other file. Never commit.
