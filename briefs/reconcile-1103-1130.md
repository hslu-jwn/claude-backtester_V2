# Brief: explain 15 "unexplained" engine-only trades at 2026-11-03 11:30 UTC (ROADMAP 12.5, runs 3 + 4)

Read `AGENTS.md` first; hard limits apply (no commits, no servers, never edit `src/backtester/live/` or
`.env`, never print credentials). Read-only investigation unless a bug in `tools/reconcile.py` is found.

Run: `python -m backtester.tools.reconcile --since 2026-11-03T11:21:00+00:00 --until 2026-11-09T08:39:00+00:00
--out results/reconcile_2026-11-09` -> 3,502 matched, 15 demo-only (2026-11-04 00:00, "bar missing in cache",
explained), 621 engine-only of which 15 unexplained, all at signal time 2026-11-03 11:30:00 UTC: AUS200,
BTCUSD, ETHUSD, EURJPY, GBPJPY, GER40, JP225, NAS100, UK100, UKOIL, US30, US500, USOIL, XAGUSD, XAUUSD.
But `results/live/probe_stdout_run3.log` (UTF-16) shows confirmed orders at 11:30:02-05 for most of them
(e.g. GER40 ticket 577255553), after 7 FX rejections "10027 autotrading disabled by client". The FX pairs
matched.

Task: find why those demo trades did not match (deal history of the new account not loaded for that
minute? comment prefix? side? the --since boundary? a symbol order effect?), using the saved live files
in `results/live/` (do not connect to MT5). If `tools/reconcile.py` is wrong, fix it test-first in
`tests/tools/` (do not weaken tests), rerun the command above and report the new counts. If not a bug,
state the explanation the tool should give. Report cause, files changed, test results.
