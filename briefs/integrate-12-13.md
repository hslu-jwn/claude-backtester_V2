# Brief: integrate strategies 12 `energy_report` and 13 `daily_reversal` (coordinator work)

Read `AGENTS.md` first; hard limits apply (no commits, no servers, no `live/`, no `.env`). Specs (gates
pre-registered, do not change rules, grids or gates): `docs/strategy-energy_report.md`,
`docs/strategy-daily_reversal.md`; their "Coordinator integration" sections list what is needed. Do NOT
run the research grids.

1. Registry: `src/backtester/strategy/registry.py` entries
   `StrategySpec("energy_report", "Strategy 12 · Energy report", EnergyReportConfig, EnergyReport)` and
   `StrategySpec("daily_reversal", "Strategy 13 · Daily reversal (Connors)", DailyReversalConfig, DailyReversal)`;
   whatever contract / registry / settings-panel tests require (fixtures, widget limits: hide research-only
   fields like timed_hold's). Golden lists: add these two only if the golden tool requires every
   registered strategy, using `python -m backtester.tools.golden --write` for the new ones only (existing
   lists must stay identical; report).
2. Data source: energy_report's spec asks for histdata explicitly in development. Check what the research
   runner does for USOIL / UKOIL 2015-2021 by default (MT5 cache starts 2021); if the default already uses
   histdata for every development day, say so and change nothing; else add the minimal grid / runner
   option the spec describes.
3. Gates: extend the gates tooling minimally so each spec's gates can be computed exactly as written:
   energy_report = the timed_hold gates with the baseline paired by `days = "report"` vs `"control"`
   (instead of `day_filter = "all"`), USOIL primary, UKOIL breadth; daily_reversal = pooled gates over 7
   indices (pooled net normal / doubled, halves, >= 4 of 7 symbols net > 0, best-5-dates removal, pooled
   bootstrap 2.5 % > 0, min 80 trades, integrity, long / short reported). Prefer flags on
   `tools/timed_hold_gates.py` over new tools; tests first in `tests/tools/`.
4. `python -m pytest tests/strategy tests/tools tests/ui tests/engine/test_ticks.py tests/golden -q` green
   (or the repo's golden test path), ruff clean. Report files, tests, the gates commands to run for each
   strategy, anything unclear.
