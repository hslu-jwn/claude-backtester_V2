# Strategy 12: Energy report

Pre-registered 2026-11-10, before any run. Registry name `energy_report`, folder
`strategy/energy_report/`, frozen `EnergyReportConfig`, strategy `EnergyReport`.
USOIL is primary; UKOIL is the breadth leg. No grid or market-data backtest was run
while writing this specification and implementation.

## Evidence and status

**PUBLISHED lead; SPECULATIVE rules.** The harvest report
`knowledge/research/reports/2026-11-10_idea_harvest_broad.md`, ideas 1, 4, 9, records
Indriawan et al. (2021, [SSRN 3822093](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3822093))
as an abstract/search-snippet lead on intraday oil predictability. Rousse and Sevi
([SSRN 2874907](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2874907)) is an
abstract/search-snippet lead on partial post-announcement reversal. Neither paper's
full text was accessible in the harvest; these rules are not a replication or a
claim of profitability. The EIA schedule was opened there; no historical release
schedule is supplied in this repository. This brief supersedes the harvest's proposed
windows and next-open convention with the explicit close execution below.

## Calendar

All event clocks use `America/New_York` via `zoneinfo`; storage and engine time are UTC.
Base timeframe M1. Clock labels below are candle **close** times: 10:29 means the M1
candle opening 10:28, and 10:45 means the candle opening 10:44.

- `days = "report"`: Wednesday, representing the usual Wednesday 10:30 EIA petroleum
  release. Skip the Wednesday if Monday, Tuesday or Wednesday of that week is a US
  federal observed holiday or an NYSE full closure. No shifted release is traded.
- `days = "control"`: Tuesdays and Thursdays, excluding a day that is an NYSE full
  closure. Other holidays in that week do not veto a control day. Early closes are not
  full closures. The two date sets are disjoint by construction.
- NYSE full closures come from the existing `timed_hold/calendars/nyse_holidays.csv`
  (including extraordinary closures). `calendar_dir`, default empty, may point to a
  replacement directory containing that file. Missing calendars fail explicitly.
- Federal rules use nationwide annual holidays, with Saturday observed Friday and
  Sunday observed Monday; Juneteenth starts in 2021. See
  [OPM federal holiday schedules](https://www.opm.gov/policy-data-oversight/pay-leave/federal-holidays/)
  and [the 2021 introduction](https://www.opm.gov/policy-data-oversight/pay-leave/federal-holidays/juneteenth-national-independence-day-holiday.pdf?stream=top).
  The local DC Inauguration Day holiday is not a nationwide holiday.

## Daily ATR

Wilder ATR(`atr_period`, default 14), in **price units**, on finished regular D1 bars
running from 17:00 NY exclusive to the following 17:00 NY inclusive. Build incrementally
from closed M1 candles; label by the ending local date and omit Saturday/Sunday labels.
Sunday evening belongs to Monday; a Sunday daytime stub never feeds ATR. Reuse
`SessionStats` with a rotated session clock. A regular day requires the exact candle
closing 17:00 (zero close tolerance, matching the shared tool's default). The initial
partial observed day follows the shared regular-close convention. No fabricated daily
candles for absent dates. True range uses the preceding regular close, seeding with
the mean of the first 14 regular true ranges, then Wilder smoothing. Today's in-progress
bar is excluded. No trade until ATR is finite and strictly positive. Warm-up request:
at least 60 calendar days, or four times `atr_period`, whichever is larger.

## Entry, stop and exit

Capture that day's exact 10:29 close. At the exact 10:45 close compute
`reaction = close(10:45) - close(10:29)`. Require a nonzero reaction and
`abs(reaction) >= k * ATR`. This is the price-unit decision by Opus, replacing the
original log-return wording. Missing either endpoint means no trade that day; no later
entry fallback. Direction is the sign of the price difference.

- Family `F` (follow, default): enter in that direction at the 10:45 close; exit at the
  candle closing 14:30 NY.
- Family `V` (fade): enter against that direction at the 10:45 close; exit at the candle
  closing 13:00 NY.
- Fixed stop `stop_atr * ATR` from entry, below for a long, mirrored for a short.
  No take profit, break-even or trailing stop. Engine execution and costs apply;
  stops are processed before signal exits. One entry attempt per date, no re-entry.
- Existing `TimedExit` convention: if the exit candle is missing, close at the first
  later available candle and record `missing_exit`; truncated data uses the engine's
  end-of-data closure and is also flagged. Such trades fail integrity. Never infer a
  missing candle's price from a later candle. Intended exits are before 17:00: expected
  swap is zero. A data hole that carries a trade over rollover is a defect, not an
  authorized overnight variant; retain actual engine swap and fail integrity.

## Grid and data

Primary: **USOIL, F, k 0.15, stop_atr 1.0, days report**. For each family, k in
{0.15, 0.30} times stop_atr in {0.5, 1.0}: 8 event cells per symbol. Each has a
matched control cell: 16 configurations x 2 symbols = 32 symbol/config evaluations,
including 16 controls. The V anchor is k 0.15, stop_atr 1.0; it is a separate
hypothesis and cannot rescue failed F. Record every cell in trial accounting.

`research/grids/energy_report.toml` has all cells and disables monkeys, sensitivity
and entry_screen, like timed_hold. **Do not run it before coordinator pre-registration
and registry integration.** Subsequent research is development-only, 2015-01-01 through
2021-09-13, explicitly from `data/cache/histdata/`. The runner's default mixed feed must
not silently substitute MT5. The MT5 holdout requires separate user authorization.
Verify both symbols' coverage before a run; lack of UKOIL is unavailable breadth, not a pass.

The documented 2020 oil jumps remain in the data (ARCHITECTURE.md, data importer):
UKOIL 2020-03-09, 45.505 -> 33.415; USOIL 2020-04-19, 18.31 -> 24.365;
2020-04-21, 21.245 -> 14; 2020-04-27, 16.605 -> 12.23 (UTC importer dates).
No clipping, deletion or special retuning; ATR and best-date-removal diagnostics
must expose their influence. Use engine costs including spread, commission and slippage;
oil news spread/slippage uncertainty remains a limitation. No fabricated zero swap
overrides; zero is expected from the intraday window.

## Gates (fixed before any run)

Follow `strategy-timed-hold.md` > Gates on development data; report each cell, decide
each family only on its registered anchor, USOIL primary and UKOIL breadth:

1. Net R > 0 at normal costs and all components doubled (report component stresses too).
2. Net R > 0 in both fixed UTC halves of the development interval.
3. Same family/k/stop: report-day mean net R minus disjoint Tuesday/Thursday control
   mean net R; independently circular-block bootstrap each ordered series, block 5
   trades, 10,000 resamples, seed 2026110. Difference's 2.5% quantile must be > 0.
   Missing either sample means insufficient evidence.
4. UKOIL net R > 0 in the matching report cell (correlated breadth, not independence).
5. Remove the best 5 trade dates; remaining net R > 0 (normal and all-doubled).
6. At least 150 USOIL report trades. Fewer means insufficient evidence.
7. No integrity failures: >5 consecutive missing M1 minutes in (entry, exit], a missing
   scheduled exit candle or any invalid present candle. Reuse the timed_hold rollover
   tolerance and also report strict counts; because valid trades never cross rollover,
   that tolerance cannot excuse missing intraday minutes here. Missing scheduled exits,
   truncated exits and unintended rollover holdings fail even if actual exit bars exist.

Report raw one-sided p-values and the local family-wise level **0.05 / 2 = 0.025**
(F and V), along with 8 event cells per symbol, all control trials and the wider
research-program trial count. These levels do not replace Gate 3's fixed quantile.
Robustness cells cannot replace a failed anchor. No pass or edge is claimed here.

## Coordinator integration

Import `EnergyReportConfig` from `backtester.strategy.energy_report.config` and
`EnergyReport` from `backtester.strategy.energy_report.strategy`, then add:

```python
StrategySpec("energy_report", "Strategy 12 · Energy report", EnergyReportConfig, EnergyReport),
```

Add an appropriate registry contract fixture with oil prices, ATR warm-up and eligible
Wednesday data. No shared files are modified in this lane.

`tools/timed_hold_gates.py` has no suitable existing CLI flag: it matches `day_filter`
against `all`, and otherwise tests mean returns rather than the required difference.
Coordinator must add an energy_report mode or separate wrapper that pairs `days=report`
with `days=control`, keeping family/k/stop identical, checks disjoint NY dates, uses
`difference_bootstrap`, sets primary USOIL / breadth UKOIL / minimum 150, and reports
the family-wise level above. Reuse `variant_report` and `rollover_integrity_failures`;
combine market-data integrity with strategy `session_records` defects for missing
scheduled exits and unexpected rollover (the generic tool checks actual exit bars).
Integrity skipped must never be presented as a pass. Registry, source selection,
contract fixture and gates integration are coordinator work before any run.

## Assumptions and decisions

- Opus 2026-11-10 decision 1: price difference versus k times price ATR; sign determines
  direction. No dimensionally inconsistent log-return comparison.
- Opus decision 2: Tuesday/Thursday control with own-day NYSE full closures skipped;
  replaces the brief's contradictory non-report-Wednesday control wording.
- Report-date proxy: Wednesday with Mon-Wed federal/NYSE holiday exclusion; no real
  historical EIA schedule. This can miss exceptional shifts and is not verified releases.
- Observed nationwide federal dates plus repository NYSE closures; no DC-only holiday,
  NYSE early-close veto or holiday-week veto on control days.
- Shared regular-close ATR convention, strict 17:00 close, weekday ending labels,
  and existing timed-exit fallback as detailed above. No current-day ATR or imputed bars.
- Same-close execution follows this brief and the engine contract; news execution costs
  are uncertain. The harvest's next-open recipes are background, superseded here.
- Two local hypothesis families, F/V; V's anchor shares the primary k/stop. Wider
  research multiplicity must still be reported by the coordinator.
- Expected no swap depends on valid exits; malformed/missing data cannot guarantee it.

## Result, development 2015-2021 (2026-11-10; `results/research/energy_report_8abe116a/`, histdata via `--cache-dir data/cache/histdata`)

**Falsified: no cell passes.** All 8 report-day cells are net negative (USOIL + UKOIL pooled):
F (follow) k 0.15 stop 0.5 / 1.0: 322 trades -7.3 / -7.5 R (primary -7.5); k 0.30: 125 trades -3.3 / -0.3 R.
V (fade) k 0.15: -49.8 / -23.9 R; k 0.30: -26.9 / -13.1 R. Gates (`timed_hold_gates --mode energy_report`):
the primary fails gates 1-5 (min trades and integrity pass). Only F k 0.30 beats its control (gate 3) but
is itself negative with 125 trades. The fade loses most: the EIA reaction does not reverse within hours.
Cells counted: 16 (8 report + 8 control) on 2 symbols.
