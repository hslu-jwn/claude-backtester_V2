# Brief: `tools/h1_shock_gates.py` (rejection gates of strategy 11)

Read `AGENTS.md` first; its hard limits apply (no commits, no servers, no `live/`, no `.env`).

## Goal

A gates tool for the development run of `research/grids/h1_shock.toml`, computing exactly the
rejection criteria in `docs/strategy-h1-shock.md` (its Gates / rejection-criteria section, copied
from `experiment.rejection_criteria` of `research/candidates/INTRADAY_H1_SHOCK_RESPONSE__v0.1.0.json`).
V2 reports, the user decides.

## Files

- New `src/backtester/tools/h1_shock_gates.py`, new `tests/tools/test_h1_shock_gates.py` (tests first).
- `docs/strategy-h1-shock.md`: a short "Gates tool" paragraph (command, output file).
- Nothing else. Do not touch `src/backtester/strategy/h1_shock/` (it is under review).

## Pattern and reuse

Follow `src/backtester/tools/timed_hold_gates.py` and `alternating_path_gates.py`: read
`variants.csv` (+ `family` column) and `variants/<id>/trades.csv` via
`backtester.analytics.records.read_trades`; reuse their helpers (stress arithmetic `STRESSES`/`net`,
`halves`, `block_bootstrap`, the gap-tolerant `integrity_failures`, `load_m1`). CLI:
`python -m backtester.tools.h1_shock_gates <research folder> [--skip-integrity]`, writes `gates.json`.

## Content

Every gate the spec lists, per cell and for the primary cell (k = 3.0, h = 1): e.g. net R at normal
and doubled costs, both development halves, the adjacent-cell sign gate (adjacent = exactly k=2/h=1,
k=4/h=1, k=3/h=2 as the JSON says), symbol / direction breadth, pooled day-clustered uncertainty
(cluster trades by entry date; report the effective event count), the mechanical mapping of the
primary cell's pooled sign to the response mode, minimum events, and data integrity. Where the spec
leaves a number open, choose the timed_hold_gates convention and say so in the report and in a
comment. Each gate is a boolean plus the numbers behind it; `advances` = all primary gates true.

## Tests

Synthetic trades (as in `tests/tools/test_timed_hold_gates.py`) for each gate's pass and fail case,
the adjacent-cell logic, day clustering (two trades on one date count as one cluster), and an
end-to-end run on a temp folder with `--skip-integrity`.

## Done =

New tests green, `python -m pytest tests/tools -q` green, `python -m ruff check .` clean. Report
files, tests, and every convention you chose.

## Decision on the first dispatch's question (Opus, 2026-11-09; write it into the spec's assumptions)

Common-event gate ("fixed subset whose complete three-hour holding interval is eligible"): use the
events actually present (traded) in all three horizon cells (h = 1, 2, 3) of the same k and response
mode, matched by symbol and signal close time (the intersection). Report its size; if it has fewer
than the spec's minimum events, the gate reads "not enough evidence" (fails). The h = 1 events flagged
three-hour eligible but suppressed in a longer horizon by cooldown are counted and reported, not used.
