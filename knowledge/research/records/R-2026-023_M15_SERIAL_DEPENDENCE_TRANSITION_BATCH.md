# R-2026-023 — M15 serial-dependence transition batch

Status: speculative compact development design; awaiting independent review and unqueued.  
Date: 2026-11-05

## Purpose and evidence boundary

Test whether a newly extreme rolling lag-one return correlation contains a short-lived directional
response. This is a dependence-state trigger, not another threshold on return magnitude, level,
range, or an exact sign pattern.

Two primary sources were opened. Bianco and Renò (2006) study FIB30 futures in 2000–2002 and find
mostly negative serial correlation below 20 minutes, attributed mainly to bid–ask bounce, but
positive correlation in high and especially unexpected-volatility regimes. Li, Giraitis and
Sucarrat (2025) use tests robust to non-stationary zero-return periodicity. On six FX pairs in
2017–2018 they find lag-one dependence at one minute is weak, short-lived and erratic; at 15
minutes, weekly-window rejection rates are generally near nominal size. Neither source tests this
local 12-pair transition rule or establishes tradable net returns.

## Four-cell design

At an eligible completed M15 boundary, form fourteen consecutive close-to-close M15 log returns.
Compute ordinary Pearson lag-one correlation over the latest twelve adjacent-return pairs and the
corresponding one-bar-lagged twelve pairs. Trigger only when the prior value is strictly neutral
(`|rho_prior|<0.30`) and the current value first reaches `rho>=0.30` or `rho<=-0.30`. A zero latest
return or zero correlation denominator suppresses the event.

`REGIME_CONSISTENT` follows the latest return after a positive transition and fades it after a
negative transition. `REGIME_INVERTED` takes the opposite side as a symmetric falsification. Cross
the two response modes with 30- and 60-minute holds: four selectable cells. Every cell has the
same chart one-ATR stop and supported executable signal-close entry; sizing uses executable
entry-to-chart-stop distance, not the chart ATR alone.

## Distinctness, advancement, and multiplicity

R010 counts a current same-sign streak, R014 requires an exact four-return alternation, and R017
measures net displacement relative to path length. R023 instead estimates centered linear
dependence between signed adjacent returns over a rolling sample. The measures remain
correlated, so results must report overlap with those three event sets and may not be described as
independent confirmation.

Each response mode advances only if its 60-minute center and 30-minute neighbor are positive under
normal and doubled costs, the center is positive in both fixed UTC development halves and at least
three symbols per half, and it survives center-derived five-date removal and a fixed-seed 95%
circular five-date bootstrap. The immutable breadth inventory is the 348 cells in
`reports/STRATEGY_THROUGHPUT_LEDGER.md` at `2026-11-05T15:11:35Z` plus this four-cell batch, for
352 selectable cells; sources and diagnostics are multiplicity context, not cells. Post-entry M1
or due-fill defects invalidate the complete affected cell rather than receiving a substituted exit.
No queue publication, execution, best-cell rescue, or holdout access is authorized by this research
record.

## Pre-review skeptical boundary

Ordinary rolling correlation is intentionally a simple implementable signal, not the robust test
proposed by Li et al.; its tiny twelve-pair window is noisy and can generate mechanical extremes.
Bid–ask bounce, zero-return periodicity, a single large return pair, and overlap with exact path
signals are material alternative explanations. The statistic concerns signed adjacent returns, not
separate return magnitudes. The adverse modern FX evidence makes the null the expected outcome.
