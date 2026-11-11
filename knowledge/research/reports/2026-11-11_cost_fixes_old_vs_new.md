# Cost fixes of 2026-11-11 (review B5, B9, B1, B8): old vs new numbers

The user's go, 2026-11-11. Each fix is its own commit with regenerated golden lists; the development
reruns below ran once after all four (`--dev-only`, separate `--results-dir
results/rerun_2026-11-11`, so the trial log and the original results are untouched). Nothing here is
a new hypothesis; no verdict changed.

## Golden lists (2023, default settings), net R per fix

| Strategy | before | B5 swap credit off | B9 USD-base commission | B1 table x live ratio | B8 short spread at exit |
|---|---|---|---|---|---|
| session_zone_sweep | -464.5 | -465.6 | -465.6 | -493.7 (2,961 trades) | -503.9 |
| no_wick | -1185.9 | -1186.2 | -1186.2 | -1213.1 (4,170) | -1224.7 |
| ny_index_sweep | -25.5 | -25.6 | -25.6 | -26.1 | -32.1 |
| opening_range | -37.9 | -38.0 | -38.0 | -39.0 | -36.6 |
| gap_fade | -24.5 | -24.5 | -24.5 | -27.0 | -26.4 |
| alternating_path | -487.7 | -487.7 | -488.3 | -488.3 | -488.3 |
| london_fix | -271.8 | -271.8 | -272.0 | -272.0 | -272.0 |
| timed_hold | 81.5 | 81.5 | 81.5 | 80.9 | 80.9 |
| trend_following | 14.6 | 14.5 | 14.5 | 14.5 | 14.4 |
| h1_shock | 0.8 | 0.8 | 0.8 | 0.6 | 0.6 |
| gap_momentum, daily_reversal, energy_report | 6.6 / 3.9 / 0 | unchanged | unchanged | unchanged | unchanged |

## Development reruns (2015-01-02..2021-09-13), pooled net R (stressed costs)

| Grid / cell | old | new |
|---|---|---|
| Gotobi G1 primary (gotobi, stop 1; USDJPY + EURJPY, 826 trades) | +32.0 (+20.4) | +31.6 (+20.0) |
| Gotobi stop 2 (826) | +17.9 (+12.2) | +17.7 (+12.0) |
| Gotobi G2 cells (946) stop 1 / 2 | +8.7 / +4.4 | +10.1 / +5.1 |
| Control "all days" (3,438) stop 2 / 1 | -6.9 / -14.1 | -4.3 / -8.8 |
| F1a fx_eu stop 0.5 (EURUSD + GBPUSD, 3,445) | +43.3 (-22.8) | +44.2 (-21.9) |
| fx_eu stop 1 | +23.8 (-9.3) | +24.3 (-8.7) |
| daily_reversal E8 target 2 / none (335 / 317) | -35.0 / -40.5 | -35.3 / -40.9 |
| daily_reversal CAP target 2 / none (32) | +5.1 / +7.2 | +5.1 / +7.2 |

Reading: the fixes move intraday clock holds by under 1 R per few hundred trades; the larger moves
are the tight-stop index / FX strategies (B1, B8), all already falsified. Gotobi's one-time test result
(not confirmed) and F1a's closure stand. Not rerun: multi-day oil / JPY-cross longs (B5 bites most
there; no live hypothesis holds them), strategy 4 on GBPJPY (its pre-registered test waits for the user).
