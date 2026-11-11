# Brief: V2.4c T-10 — Bayesian report for the chosen variant (and A/B for filter twins)

Context: ROADMAP › V2.4c (accepted by the user 2026-10-23); idea card T-10 in
`knowledge/ideas.md` (prior odds **1:50 against an edge**, set by the user 2026-10-16);
`knowledge/books/kurt-bayesian-statistics.md` (WK ch.5, 9, 13-19, notes M1-M10);
`knowledge/topics/statistics-and-bayes.md`. Pure analytics, no trading rule changes.

## What to build (`analytics/bayes.py`, wired into the research runner)

1. **Win rate** of a trade list (win = r_net > 0) under three Beta priors, centred on the
   break-even win rate p* = |avg loss| / (avg win + |avg loss|) of that same list:
   flat Beta(1, 1); weak skeptical, strength 20 (alpha + beta = 20, mean p*); strong skeptical,
   strength 100 (configurable; the card says 100-200, default 100, say so in the spec as an
   Opus choice the user can change). Per prior: posterior mean, 95 % interval,
   P(win rate > p*).
2. **Mean R per trade**: posterior with a skeptical Normal(0, 0.075 R) prior on the mean and
   the sample's sd (normal-normal with known variance is fine; say so), 95 % interval,
   P(mean R > 0). Use the **effective trade count** from `analytics/effective_n.py` (V2.4d 5)
   instead of n when trades overlap, and report both.
3. **Bayes factor** edge vs no edge for the win rate (WK ch.16-17: H1 Beta posterior vs H0 point
   p*), posterior odds with the prior odds 1:50, and **trades needed** to reach posterior odds
   of 10:1 if the observed win-rate edge were real (closed form or a small search).
4. **A/B for filter twins** (research runner `compare_to` families): P(B > A) for the mean R by
   sampling both posteriors (seeded, 20,000 draws), and for the win rate.
5. **Runner**: report block "Bayesian view" for the chosen variant (development, and test once
   run) and per twin family; `bayes.json`. A flag `bayes_weak` on the chosen variant when
   P(mean R > 0) under the skeptical prior is below 0.9. Resumable, cheap.

## Rules

Spec first (`docs/research-runner.md` › a "Bayesian view" section with the priors and the
1:50 odds), the test-case list at the top of the test file, failing tests, then code. Tests with
known answers: Beta-binomial posterior numbers against closed form; a list exactly at p*
-> P(win > p*) about 0.5 under the flat prior; a stronger prior pulls toward p*; more trades
narrow the interval; P(B > A) about 0.5 for identical lists and near 1 for a clearly better B;
trades-needed matches the card's example (55 % vs 50 % at 1:50 needs about 1,400 trades, a
loose check). Selection, test run, trial log, DSR and all numbers unchanged. Never edit
`src/backtester/live/`.

Done = full suite green (`pytest -q > results\pytest_t10.log 2>&1`), `ruff check .` clean.
Report: files changed, test count, decisions the spec did not settle, open questions.
