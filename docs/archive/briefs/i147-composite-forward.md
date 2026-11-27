# Brief: I-147 flow + carry composite, forward logger + canary (no data look)

Worker: Claude Sonnet subagent. Coordinator: Opus. Read first: `AGENTS.md`; the card `knowledge/ideas.md` › I-147
(frozen rule; never change it); `docs/research-runner.md` › M13 (rule P).

## Reuse (read before writing code)
- `src/backtester/tools/crypto_flow.py`: Strategy 20's loader (`load`), week building, `append_forward` (append-only
  checks: columns, duplicate week, out-of-order week, data changed under the log). Copy that pattern.
- `research/screens/2026-11-14_i78_crypto_wide_factors_screen.py`: `mondays`, `week_rows` (eligibility, flow, ret,
  fund) and I-78's development run (the canary target).
- `research/screens/2026-11-19_i133_crypto_composite_screen.py`: funding sum per week (`weeks_table`), 7-day funding
  history rule.
- `research/screens/2026-11-15_wave1_xs_crypto_screen.py`: I-83 residual and I-84 perp-minus-spot flow (spot bars).

## Build
1. `research/screens/2026-11-27_i147_composite_forward.py` with modes:
   - `canary`: f2 = f3 = c = 0, quintile bins, I-78's universe / period / 20 bp cost: must print I-78's development
     headline +145.0 bp a week, t 3.24 (to the reported precision). If it does not reproduce, stop and report why;
     never tune anything to make it match.
   - `forward`: for every complete week from Monday 2026-11-30 (Monday open to next Monday open) not yet logged, build
     the top-100 universe and S exactly as the card says, the target weights with the 0.005 no-trade buffer against
     the previous logged weights, and append one row to `research/forward/i147.csv` (week, names, gross bp, funding
     bp, traded notional, cost at 10 bp, net at 10 / 20 / 5 bp, f3 coverage, dispersion state) plus the weights to
     `research/forward/i147_weights.csv`. A week with < 40 names is logged as skipped. Today no week is complete, so the
     command must say "no complete forward week" and write nothing.
   - `--selfcheck` (asserts) is fine but the tests below are required.
2. `tests/tools/test_i147_composite.py` (hand-built fixtures, `tmp_path` only): rank-normal score
   Phi^-1((rank - 0.5) / N); F re-standardised to unit sd and missing f3 handled; clip(-2, 2), mean removed, long sum 1
   and short sum 1; buffer keeps the old weight below 0.005 and trades above; cost only on traded notional; < 40 names
   skipped; funding signal uses only settlements in (Monday - 7 d, Monday]; appending future days never changes a
   logged row; duplicate / out-of-order / changed-data appends raise.

## Allowed / forbidden
- May create only the two files above and `research/forward/` outputs of a real `forward` run (expected: none today).
- **No data look:** never compute the composite (any S-sorted return) on any historical week. The canary is the only
  historical run and uses I-78's rule only. Retro pool members P1 / P2 are computed later by Opus at the first look.
- No commits / pushes / branches; no servers or lasting processes; no credentials; never edit `src/backtester/live/`,
  `.env`, `src/backtester/tools/notify.py`; no package installs. Downloads only through the existing Binance tools if a
  cache day is missing, and say so.
- `ruff check` + `ruff format` on your two files; run your tests.

## Done =
Tests green, ruff clean, canary output pasted, `forward` dry output pasted, list of every assumption you made.
