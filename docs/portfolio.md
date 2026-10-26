# Portfolio (V2.7)

The Portfolio tab next to Research compares combinations chosen by the user. It never
computes or displays holdout results. Trading rules and strategy/risk defaults are unchanged.
Only chosen research variants with complete saved development `daily.csv` and `trades.csv`
are eligible. Research development dates, saved-run dates, daily dates and trade timestamps
must be before 2021-09-14. Missing or invalid members are reported, never backtested to repair
them. Flags come only from the development variant row, never test diagnostics.

## Search metrics

Pick 2–12 members, then Find combinations. All sets of 2–4 are enumerated (781 at twelve).
Weights are 1/N, without optimisation or IDM scaling. Each set uses the intersection of its
members' saved days. Daily R is `net_r_exit_booked`: Prague weekdays, zero-trade days retained.
Union days lost and days dropped per member are reported. Fewer than 250 common days is a
warning, including no overlap; no set is removed. Undefined ratios and empty-set metrics
are null, never infinity. No pass/fail verdicts are assigned.

- Net R: sum of equally weighted daily R.
- Maximum drawdown (R): running equity peak minus equity, including initial zero equity.
- Net R / max DD: undefined when max DD is zero.
- Daily Sharpe: sample standard deviation (ddof=1), mean / SD × sqrt(252).
- Worst month: smallest calendar-month sum, including partial boundary months.
- Longest drawdown: maximum consecutive observed trading days below a prior peak, including
  an unrecovered final drawdown; recovery day is not counted.
- Correlation: Pearson on common days, joint zero days retained. Shared portfolio convention:
  constant members have zero off-diagonal correlation, diagonal one.
- IDM: shared `analytics.portfolio.idm`, negative correlations floored at zero, cap 2.5;
  displayed only, never applied.

Leave-one-out recomputes these metrics on the remaining members' common development days,
with equal weights renormalised. Removing one of two leaves exactly the single member.
The detail view shows equity, correlation, regimes and leave-one-out metrics.

## Regime attribution

Use the existing D1 classifier and its defaults (`regime-classifier.md`), looking up each
symbol's last confirmed label at midnight Europe/Prague at the **start** of each reporting
day. No unfinished D1 is used. Insufficient history stays unknown. Candle loading stops
within the development period and never fetches test candles.

For a multi-symbol set, show a separate breakdown of the **whole combined daily R** against
each member symbol's daily regime. This avoids an arbitrary vote between different markets.
Each breakdown reports day count, net R and R/day; it is conditional attribution, not the
contribution of that symbol's trades. Different symbols' tables overlap and must not be added.
This attribution convention is for user review; it changes no trading or classifier rule.

## Saved searches and Monte Carlo

`results/portfolio/search_<pool-hash>.json` caches all search details. The hash includes
member identities, daily content, saved settings, saved trade/run file fingerprints and schema
version; pool order is irrelevant.
Set IDs hash the JSON list of sorted member IDs, so order cannot change identity.

Sort the table (default net R / max DD descending), then Monte Carlo top 10. Undefined values
rank last. One queue job per set calls `tools.portfolio --existing <members.json>` and reuses
the saved member trades over the common development period. No member backtest, alternative
strategy backtest or random-path strategy replay is run. Existing Monte Carlo/prop-firm
machinery uses its defaults. Kind B is unavailable without saved alternatives; kind C uses
the existing component-wise weighted fill simulation using each member's saved cost settings.
Weekend exits follow the shared daily-R booking rule. Active/completed jobs with unchanged
input are reused. The shared queue panel shows jobs and controls the runner; enqueueing
does not start a process.

Development results live at `results/portfolio/<set-id>/summary.json` and `report.html`.
The page shows pass probability and median days to pass for each existing risk level, with
no portfolio verdict (the development HTML report also omits the verdict banner/checklist).
The page polls for finished reports and refuses non-development or
stale summaries.

## One-time test (CLI only)

After choosing the member set, run:

```text
python -m backtester.tools.portfolio --test <set-id>
```

The saved manifest fixes member identities and settings. Each member runs once on MT5-only
data from 2021-09-14 through the last day available to every symbol (optional `--end`), with
equal weights. It does not run kind-B alternative strategies. The trial log records the
attempt before backtesting and the finished result after backtesting. An exclusive permanent
reservation is written before execution. Failed/interrupted attempts count: reruns of the
same sorted member IDs are refused even when end dates or input order change. No retest flag.
Holdout artifacts are isolated at `results/portfolio/tests/<set-id>/`; the page never reads them.
There is no UI action to run or queue a test. Legacy components-file CLI usage remains available.

Visual acceptance and independent cross-review remain with the user/Opus. No app is started
as part of this build.
