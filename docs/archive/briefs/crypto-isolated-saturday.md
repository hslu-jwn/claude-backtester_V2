# Brief: isolated missing Saturdays of BTCUSD / ETHUSD are closures, not segment cuts (follow-up to 52a0d4d)

Read `AGENTS.md` first; hard limits apply (no commits, no servers, no `live/`, no `.env`). Test first; never
weaken a test. Audit: `knowledge/research/reports/2026-11-10_crypto_segment_cuts.md` (read it).

Decision by Opus (2026-11-10, data-handling rule, recorded in `docs/research-runner.md`): for BTCUSD and
ETHUSD, a missing Saturday cache day whose Friday and Sunday are present is a broker closure (FTMO crypto
CFDs closed on Saturdays before 2022), not a data gap, in every year. Any other missing day or a longer hole
still cuts. Extend the yearly rule of 52a0d4d minimally (keep it symbol-scoped; FX and all other symbols
unchanged; golden lists identical).

Tests: a crypto-like cache with some Saturdays present and isolated Saturdays missing -> no cut at the
isolated Saturdays; a missing Saturday next to a missing Sunday still cuts; FX unchanged. Then rerun
`python -m backtester.tools.research research/grids/trend_following_crypto.toml --dev-only` and the `_eth`
grid (unchanged grids), report segments and per-cell trades / net R. `python -m pytest tests/data tests/tools
tests/golden tests/test_runner*.py -q` green, ruff clean. Report files, tests, output.
