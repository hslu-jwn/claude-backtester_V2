# Strategy 11: H1 shock response (draft)

**Status: implementation draft; Opus review required before any research run.**

Sources: `research/candidates/INTRADAY_H1_SHOCK_RESPONSE__v0.1.0.json` (v0.1.0)
and `knowledge/research/records/R-2026-004_INTRADAY_SHOCK_RESPONSE.md`.
This is a sign-agnostic falsification re-study; prior I-61 trials remain counted.
The supplied Opus decisions of 2026-11-09 replace the older session masks, calendar
dependency and strict completeness requirement. Other quoted rules remain unchanged.

## Hypothesis

> The direction-normalized return after an unusually large completed H1 move has a stable non-zero sign over the next one to three hours.

> Continuation may reflect information diffusion or persistent order flow; reversal may reflect temporary liquidity pressure or overreaction. Both signs are tested and the zero-after-cost null is preferred absent broad stability.

## Definitions

Universe: XAUUSD, GBPUSD, GBPJPY, NAS100, US500.
Use M1 open timestamps, half-open local-clock H1 intervals, and UTC storage.
London clock: XAUUSD/GBPUSD/GBPJPY; New York clock: NAS100/US500. Use IANA zones.

> Aggregate M1 intervals [t,t+1m) into local H1 intervals [H,H+1h) using Europe/London for XAUUSD, GBPUSD, and GBPJPY and America/New_York for NAS100 and US500

### `event_return_s_H`

> ln(close_s_H/open_s_H) for the completed per-symbol IANA local-clock H1 event bar represented by UTC boundaries

> Known only at H1 close H+1h

### `q_s_H_h`

> sign(event_return_s_H) * ln(close_s_H_plus_h/close_s_H), using the exact h-hour causal forward close for the same eligible event; positive q means continuation and negative q means reversal

> An outcome known only at the scheduled h-hour evaluation close; never available to entry selection

### `robust_z_s_H`

> (event_return_s_H-median(W60_s_clock))/(1.4826*MAD(W60_s_clock)), where W60 contains only the previous 60 valid returns for the same symbol and IANA local clock hour; skip the event when MAD is zero or non-finite

> Window ends before the event bar and never includes current or future data

### `trade_side_s_H`

> sign(event_return_s_H) for CONTINUATION and -sign(event_return_s_H) for REVERSAL

> Frozen at the event H1 close

### `stop_distance_s_H`

> 6.0 * WilderATR20_H1_s_H

> Computed from completed H1 bars at entry and never widened

### `event_cost_multiple_s_H`

> abs(close_s_H-open_s_H) / (2 * resolved_one_way_signal_price_cost_s_H), where the one-way denominator component is the deterministic V2 spread plus commission plus slippage schedule resolved at the signal timestamp and expressed in symbol price units

> Computed causally at signal time from the authoritative V2 cost schedule, identically for every response mode and holding horizon; never use a future exit schedule or realized quote and skip if non-finite or non-positive

W60 is per symbol and local clock hour. Evaluate z before appending the current valid
return. Prior events and entry-ineligible bars remain eligible when structurally valid
under the supplied expected-M1 schedule. Never filter W60 by future outcomes.

## Rule

> weekday AND abs(robust_z_s_H)>=event_z_threshold AND event_cost_multiple_s_H>=minimum_event_cost_multiple AND trade_side_s_H=+1 AND the completed event bar and proposed holding interval pass every deterministic calendar/session exclusion knowable at signal time AND no position or horizon cooldown is active for the symbol within this independently executed grid cell

> weekday AND abs(robust_z_s_H)>=event_z_threshold AND event_cost_multiple_s_H>=minimum_event_cost_multiple AND trade_side_s_H=-1 AND the completed event bar and proposed holding interval pass every deterministic calendar/session exclusion knowable at signal time AND no position or horizon cooldown is active for the symbol within this independently executed grid cell

> Fill at the event H1 close under V2 costs; never use the event high or low and never substitute next-bar-open

The first eight older restriction clauses are superseded by the supplied decisions below.
Remaining restrictions, verbatim:

> Reject each symbol's local-calendar day when its session timezone changes UTC offset

> Only the first eligible event per symbol is allowed until its holding interval expires; overlapping events are ignored

> Each of the 18 grid cells is executed with independent position and cooldown state; state from one cell must never suppress an event in another cell

> After any entry, that cell's symbol remains in horizon cooldown until the originally scheduled time exit even if the safety stop closes the trade early

> Require finite non-zero MAD, finite positive ATR, and all 60 prior same-clock observations

> Never remove an observation from W60 because of its return magnitude, event label, trade eligibility, or later outcome

> Require the absolute event move to cover at least five resolved round-trip price-cost units; the multiplier is fixed and cannot be optimized

> The event cost floor uses twice the one-way deterministic price cost resolved at the signal timestamp and is identical across holding horizons; never use a future exit schedule or realized quote for event selection

> Do not use opening gaps, opening ranges, or final-30-minute returns as signals

## Exits

> Long: entry_price-stop_distance_s_H; short: entry_price+stop_distance_s_H; fixed at entry under V2 adverse fill rules

> Close on the first completed M1 bar ending exactly holding_hours*60 minutes after the signal close

> Skip the entry unless its scheduled holding interval ends by the applicable predeclared cutoff. If data corruption prevents an entered position from being observed through its planned exit, mark the experiment TEST_FAILED; never backfill an exit at an earlier bar

No profit target. Priority: STOP_LOSS, TIME_EXIT, END_OF_SESSION_FORCE_CLOSE.
Reuse `strategy/session_stats.py` (`TimedExit`). Missing exact-exit candles are integrity
failures; a later observed exit must never be represented as the planned exit price.

## Risk

> Size so initial entry-to-stop risk equals 0.10% of current equity before costs; never resize or widen

> Maximum five concurrent positions and 0.50% aggregate initial stop risk

> Use the lower of stop-risk size and V2 limits; skip if the position cannot be represented

> Within each independently executed grid cell, at most one position per symbol and five positions total; correlated cross-symbol events remain separate trades but are aggregated by date for inference

Strategies output stop-defined R; equity sizing belongs to the risk layer.

## Grid and primary setting

Exactly 18 independently executed cells, as experiment.total_grid_size requires.

| Cell | Response mode | k | h (hours) |
|---|---|---|---|
| 1 | CONTINUATION | 2.0 | 1 |
| 2 | CONTINUATION | 2.0 | 2 |
| 3 | CONTINUATION | 2.0 | 3 |
| 4 | CONTINUATION | 3.0 | 1 |
| 5 | CONTINUATION | 3.0 | 2 |
| 6 | CONTINUATION | 3.0 | 3 |
| 7 | CONTINUATION | 4.0 | 1 |
| 8 | CONTINUATION | 4.0 | 2 |
| 9 | CONTINUATION | 4.0 | 3 |
| 10 | REVERSAL | 2.0 | 1 |
| 11 | REVERSAL | 2.0 | 2 |
| 12 | REVERSAL | 2.0 | 3 |
| 13 | REVERSAL | 3.0 | 1 |
| 14 | REVERSAL | 3.0 | 2 |
| 15 | REVERSAL | 3.0 | 3 |
| 16 | REVERSAL | 4.0 | 1 |
| 17 | REVERSAL | 4.0 | 2 |
| 18 | REVERSAL | 4.0 | 3 |

> Primary diagnostic setting: event_z_threshold=3.0 and holding_hours=1. Map positive pooled q to CONTINUATION and negative pooled q to REVERSAL; both response-mode cells remain counted and no non-primary cell may rescue a failed primary setting.

| Parameter | Default | Domain |
|---|---|---|
| response_mode | CONTINUATION | CONTINUATION, REVERSAL |
| event_z_threshold | 3.0 | 2.0, 3.0, 4.0 |
| holding_hours | 1 | 1, 2, 3 |
| same_clock_lookback | 60 | fixed |
| atr_period_h1 | 20 | fixed |
| stop_atr_multiplier | 6.0 | fixed |
| minimum_event_cost_multiple | 5.0 | fixed |
| risk_fraction_equity | 0.001 | fixed |

Grid switches: `monkeys = false`, `sensitivity = false`, `entry_screen = false`.
Do not run the research grid before Opus reviews the spec; holdout requires user authorization.

## Gates (verbatim rejection criteria)

> Reject the family if the k=3.0, h=1 primary setting fails any mandatory net, breadth, half-sample, concentration, common-event, or doubled-cost gate; no other cell may rescue it

> Reject if the primary pooled raw q two-sided day-clustered 95% confidence interval includes zero or if the mechanically mapped response mode's day-clustered 95% confidence interval for mean net R includes zero or extends below zero

> Reject if neither response mode has positive pooled net R in both development halves

> Reject if the primary setting's mechanically mapped response mode has positive gross expectancy on fewer than three of five symbols; a supporting symbol is exactly a symbol whose primary raw mean q has the pooled primary q sign and therefore whose mapped-mode gross expectancy is positive

> Reject if fewer than 100 pooled events or fewer than 20 primary events exist for each supporting symbol as defined by the frozen gross-sign breadth gate

> Reject if removing the five most profitable events makes pooled net R non-positive

> Reject if the primary response-mode cell is non-positive under doubled costs

> Reject if any of the exactly predeclared adjacent cells k=2/h=1, k=4/h=1, or k=3/h=2 does not preserve the primary pooled q sign

> Reject if the fixed common three-hour-eligible event subset reverses the primary sign

> If this re-study fails, reject further re-specification of the same shock-response family on the existing development data

> Never run the final holdout without later explicit user authorization for an independently reviewed immutable version

## Required experiment reporting (verbatim)

> Report all 18 response-mode by threshold by horizon cells and count all 18 trials

> Report each symbol, event direction, IANA local clock hour, and both fixed development halves without post hoc selection

> Report each horizon on its own predeclared eligible sample and all horizons on the fixed subset whose complete three-hour holding interval is eligible; this is report-only

> Treat event_z_threshold=3.0 and holding_hours=1 as the sole primary setting; map its pooled q sign mechanically to response mode and use all other cells only for robustness

> For the mandatory adjacent-cell sign gate, adjacent means exactly k=2/h=1, k=4/h=1, and k=3/h=2; k=3/h=3 remains reported but is not called adjacent

> Report pooled day-clustered uncertainty and effective event count

> For the primary k=3/h=1 setting report a two-sided day-clustered 95% confidence interval for mean raw q and a day-clustered 95% confidence interval for the mechanically mapped mode's mean net R; both are mandatory gates rather than descriptive outputs

> Remove the largest one and five profitable events and report March 2020 separately

> Compare with same-clock non-event returns and shuffled event signs

> Report stop frequency; a frequently hit safety stop means the time-exit study was materially altered

> Repeat net accounting under doubled spread, commission, and slippage

> Publish the compact decision summaries frozen in Research_Department/reports/R004_CANONICAL_RESULT_MAP.md under canonical result robustness.r004: calendar and integrity identity, exactly 18 complete cell rows, deterministic primary selector, mapped-mode diagnostics, every required split/sample/check, and an explicit status and reason for every skipped or failed diagnostic

## Costs and multiple testing (verbatim)

> Use resolved V2 spread, commission, slippage, and any applicable financing without research overrides

> Session eligibility is intended to avoid broker rollover; disclose and charge any real swap rather than assuming same-day means zero swap

> Include doubled spread, commission, and slippage stress

> Count exactly 18 strategy cells plus every registered prior V2 trial, including the failed I-61 family. Symbols, directions, clock hours, halves, and event exclusions are reporting splits and may not become post hoc selection parameters.

## Assumptions (supplied Opus decisions, 2026-11-09)

- NAS100/US500: New York clock; eligible event bars and holding intervals only inside
  NYSE regular hours 09:30-16:00 on NYSE trading days, excluding 09:30-10:00 and
  15:30-16:00. Skip full closures and early-close days. Import the NYSE calendar
  loader in `strategy/timed_hold/day_filter.py`; do not copy the CSV.
- XAUUSD/GBPUSD/GBPJPY: London clock; weekdays; exclude 21:00-23:59 London
  and the first two hours after Sunday reopen; no other holiday calendar.
- Robust-z uses only completed event bars before the signal.
- Stale/non-advancing OHLC: at least 15 consecutive flat M1 candles
  (open = high = low = close) at one unchanged price inside an eligible window.
  An H1 containing such a run is invalid; single or short runs are legitimate.
- Expected-M1 schedule replaces the missing authoritative CFD calendar for entries,
  integrity checks and W60 alike. For indices: every minute of 09:30-16:00 New York
  on NYSE trading days; full closures and early-close days are not trading days.
- For XAUUSD/GBPUSD/GBPJPY: Monday-Friday 00:00-21:00 London. Sunday reopen
  (about 22:00 London) plus two hours ends Monday 00:00; no Sunday minute is eligible.
  Exclude 21:00-23:59 daily.
- An H1 event bar is valid only with at least 55 of 60 expected M1 candles,
  no run of more than five missing minutes, and no stale run. Invalid bars are
  neither events nor W60 observations; W60 counts only valid bars.
- Keep and report entered trades whose holding intervals later break integrity rules
  (the gate tool integrity count). TEST_FAILED applies to the experiment report,
  not to dropping trades from the backtest.

- Boundary candles (Opus, 2026-11-09): first and last M1 candles must both be
  present in every valid H1 bar, for events and W60; missing minutes are interior only.

## Assumptions: implementation conventions (additional)

- Wilder ATR uses valid completed H1 bars, including the signal bar. Seed with the
  arithmetic mean of the first 20 true ranges, then recurse; invalid bars do not update
  ATR or its previous close. True range includes gaps from the preceding valid close.
- One-way signal-price cost = resolved spread + half the round-turn commission + one
  market-fill slippage. Evaluate percentage commission at the signal bid close. Use
  the same cost floor for both directions; actual execution costs are charged by V2.
- Reuse TimedExit's first-later-candle fallback when the exact exit is absent. Report
  the missing exit as an integrity defect and retain the actual later fill timestamp.
- Request at least 120 calendar days of warm-up; still require all W60 observations.
- Each instance owns symbol/cell state. Skipped orders release position and cooldown;
  an early stop retains the original horizon cooldown.
- Session records expose signal statistics and per-trade integrity defects for later
  gate reporting. The strategy does not evaluate experiment gates.

The supplied boundary decision resolves the previous blocker. No research grid has run.

## Gates tool

Run `python -m backtester.tools.h1_shock_gates <research folder> [--skip-integrity]`.
It writes `gates.json` in that folder. Raw q requires cached M1 data even when the
integrity check is skipped. A skipped integrity check is identified in the output.

## Assumption: common-event gate (Opus, 2026-11-09)

Use the intersection of events actually traded in all three horizon cells of the same
threshold and response mode, matched by symbol and signal close time. Report its size;
if fewer than 100 events remain, the gate fails with "not enough evidence". Count and
report h=1 events marked three-hour eligible that are absent from a longer horizon;
they are not included in the common subset.

## Codex sol read-only review (2026-11-09, before the run)

Spec vs code and lookahead (`results/ai/20261109-153255_codex_review-h1-shock.md`): no future
candle access (W60 excludes the current return, ATR includes the completed signal bar as specified),
thresholds, response sides, 6 x ATR stop, horizon exits, session masks, validity rules, cooldown and
the 18-cell grid match the spec; the engine cost hook affects only this strategy. One conditional
finding: dates outside the NYSE calendar's coverage (2008-2026) are accepted as trading days; the
development data (2015-2021) is inside it, so no effect on this run.

## Result, development run (2026-11-09, `--dev-only`, 2015-2021; test period untouched)

`results/research/h1_shock_1d710243` (`gates.json` by `tools/h1_shock_gates.py`). **Falsified: no cell
advances.** All 18 cells are net negative: CONTINUATION k 2 / 3 / 4: -0.012 / -0.009 / -0.007 R per
trade at h = 1 (8,460 / 3,697 / 1,821 trades), best cell k = 4, h = 3: -1.0 R over 1,172 trades;
REVERSAL every cell -0.011 to -0.022 R per trade. Primary (k = 3, h = 1): raw direction-normalized
response q mean +0.00003, 2.5-97.5 % interval -0.00013 / +0.00019 (3,693 events, 1,113 date clusters),
so no response mode is mapped and every dependent gate fails. Large H1 moves carry no tradable
follow-through either way after costs, the same reading as I-61 (2026-10-20). 18 cells counted.
