# Brief: time-of-day profile tool (research screening)

Read `AGENTS.md` first. Hard limits there apply (no commits, no servers, no `live/`, no `.env`).

## Goal

A read-only research tool that shows, per symbol, the mean return per local clock hour on the
**development period only** (before 2021-09-14), next to the symbol's round-trip cost, so a
time-of-day hypothesis can be screened against costs before a grid is built
(`knowledge/topics/cost-wall.md`). It replaces the one-off placebo script of 2026-11-09
(`docs/strategy-timed-hold.md` › Run 1 follow-ups).

## Files

- New: `src/backtester/tools/time_of_day_profile.py`
- New: `tests/tools/test_time_of_day_profile.py` (write first)
- Nothing else.

## Behaviour

```
python -m backtester.tools.time_of_day_profile EURUSD GBPUSD --zone Europe/London \
    [--start 2015-01-01] [--end 2021-09-13] [--split 2018-07-01] [--out results/tod_profile]
```

- Load M1 with `backtester.tools.entry_screen.load_m1(symbol, DEFAULT_SOURCES, start, end)`.
  `--end` defaults to 2021-09-13 and must be refused (SystemExit with a clear message) if later
  than 2021-09-13 (the fixed development/test split, `docs/research-runner.md`).
- For each local hour h (0-23 in `--zone`, DST via `zoneinfo`) and each weekday date: return from
  the close of the M1 candle closing at h:00 to the close of the candle closing at (h+1):00 local.
  Skip the pair if either candle is missing (no fill-forward). Returns in price units and in
  basis points (100 * 100 * ln(p1/p0)).
- Per hour: n, mean bp, t-stat (mean / (sd / sqrt n)), and the same for the sub-periods before and
  on/after `--split` (default: the midpoint of start..end).
- Cost line: the round-trip cost in bp at the median price, from the engine cost model
  (`backtester.engine.costs.CostConfig()` default: spread + 2 x slippage + commission, the
  stop-out case, as in `knowledge/research/reports/2026-11-09_cost_in_R_table.md`; read how
  `CostConfig` gives spread / slippage / commission for a symbol and price).
- Output: `<out>/<symbol>.csv` (hour, n, mean_bp, t, mean_bp_first, t_first, mean_bp_second,
  t_second) and a short `<out>/report.md` (one table per symbol plus the cost line in bp and the
  hours whose |mean_bp| exceeds the cost). Print the report path.

## Tests (hand-built M1 data, no cache access: monkeypatch `load_m1` or pass arrays to a pure
function you factor out)

1. A synthetic series rising 1 bp in every 08:00-09:00 London hour and flat otherwise: hour 8
   mean = 1 bp, other hours 0, n = number of weekdays.
2. DST: the same local hour maps to 07:00 UTC in summer and 08:00 UTC in winter.
3. A missing candle at h:00 or (h+1):00 drops that day for that hour only.
4. Weekends are excluded.
5. `--end 2021-09-14` is refused; the default end is 2021-09-13.
6. The split puts dates before `--split` in "first", the rest in "second".

## Done =

New tests green, `python -m pytest tests/tools -q` green, `python -m ruff check .` clean. Report:
files created, test counts, anything unclear.
