# Brief: V2.4d item 5 + V2.4c T-09 / T-19 — best-of-N significance, PBO, effective N

Context: ROADMAP › V2.4d (5) and V2.4c (accepted by the user 2026-10-23);
`docs/review/book-app-requirements.md` E2, E3, E6, E9; `knowledge/topics/testing-and-robustness.md`
› False discoveries and checklist 23-25, 29, 34; book notes `knowledge/books/aronson-evidence-based-ta.md`
(White's Reality Check, Monte Carlo permutation, ch.6), `masters-testing-tuning.md` (ch.5 CSCV,
ch.7), `lopezdeprado-afml-ch1-11.md` / `-ch12-22.md` (CPCV, PBO, uniqueness weights).

Since V2.4d 1+2 every research variant keeps its daily series (`variants/<id>/daily.csv`:
`net_r_exit_booked`, `net_r_mtm`, `position`; `trial_log.series_matrix(records, kind)`). Build the
tests on the **marked-to-market** series (`net_r_mtm`).

## What to build (pure functions in `analytics/`, wired into the research runner)

1. **White's Reality Check** (`analytics/best_of_n.py`): statistic = the best variant's mean
   daily R; null = every variant's series centred to mean 0; `boots` (default 2000) stationary
   bootstrap resamples of the **day indices, the same indices for all variants**
   (`risk/bootstrap.stationary_orders`, mean block 5 days); p = share of resamples whose max
   centred mean >= the observed max (with the +1 correction). Also Hansen's SPA-style
   studentised version only if it is a few lines; otherwise not.
2. **No permutation test in this brief.** The Monte Carlo permutation best-of-N test (Aronson
   ch.6, Masters ch.7) needs the variants re-run on permuted prices; the saved series cannot
   provide that, and a sign-flip of saved returns is not a valid null for trading rules. Write
   in the spec that it comes in V2.6 with the job queue (MCPT of the whole optimisation).
3. **CSCV / PBO** (`analytics/pbo.py`, Bailey-Borwein-López de Prado-Zhu as in Masters ch.5 /
   AFML ch.11): matrix days x variants, split into S (default 16, even) blocks in time order,
   all C(S, S/2) combinations as in-sample; pick the variant with the best in-sample Sharpe,
   rank it out of sample; logit of the relative rank; PBO = share of logits <= 0. Also report
   the median OOS rank and the in-sample vs OOS performance pairs (degradation slope). Purge:
   drop `purge_days` (default 5) at each block boundary from the OOS side. Fewer than 2
   variants or too few days: "n/a" with the reason.
4. **Effective N** (`analytics/effective_n.py`): (a) for the trials: the number of independent
   variants from the average pairwise correlation of the daily series
   (N_eff = N / (1 + (N - 1) x mean correlation), floor 1), reported next to N; (b) for trades:
   López de Prado's average uniqueness (concurrent open trades per day, `position` series or
   the trades' open intervals) and the effective trade count = sum of uniqueness weights.
   Do **not** change the DSR's N yet; report N_eff beside it (the user decides later).
5. **Runner wiring** (`tools/research.py`): after the development phase, compute the three on
   the development variants (sensitivity neighbours excluded, they are not a selection) and write
   `significance.json` + a report block "Is the best variant better than luck?": RC p-value,
   PBO, median OOS rank, N and N_eff, effective trades of the chosen variant. Warning flags on
   the chosen variant: `rc_not_significant` (p > 0.05), `pbo_high` (PBO >= 0.5),
   in `analytics/scorecard.py` FLAG_LABELS. Resumable; cheap enough to recompute every run.

## Rules

Spec first (`docs/research-runner.md` › a new section "Significance of the best variant", and
`docs/risk-management.md` › Trial log and deflated Sharpe for N_eff), the test-case list at the
top of each new test file, failing tests, then code. Tests with hand-built matrices where the
answer is known: identical variants -> N_eff 1; independent noise -> N_eff ~ N; one variant
with a planted large edge -> RC p small and PBO low; pure noise variants -> RC p roughly
uniform (seeded, a loose check) and PBO near 0.5; the same day indices for all variants in a
resample; S odd / too few days -> clear error or n/a. Selection, the test run, the trial log,
the DSR and all existing numbers stay unchanged. Never edit `src/backtester/live/`.

Done = full suite green (`pytest -q > results\pytest_v24d5.log 2>&1`), `ruff check .` clean.
Then run the runner once on `research/grids/orb.toml --dev-only --results-dir
results\v24d5_check` (log file; it may take ~10-20 min) and put its significance block in the
report. Report: files changed, test count, decisions the spec did not settle, open questions.
