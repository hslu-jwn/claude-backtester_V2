# R-2026-009 — M15 wick-rejection response batch

Status: speculative high-throughput development design; unreviewed and unqueued.  
Date: 2026-11-05

## Purpose and evidence boundary

Test whether completed-candle rejection geometry has incremental short-horizon information after
costs. This is a distinct candle-geometry family rather than another return shock or compression
break: entry depends on the wick fraction and close location of one completed M15 candle, not on a
large close-to-close return or a close outside a prior range.

The frozen V2 backlog attributes outside-bar/key-reversal and range-filter context to Perry J.
Kaufman's *Trading Systems and Methods*, pages 111 and 157-158, without identifying the edition.
Wiley's catalog verifies the current sixth edition's author, title, 2019 date, and ISBN, but does
not establish that the legacy page references map to that edition; the cited pages were not
independently opened in this session. No inspected academic or cost-aware M15 FX result supports
the local rule. The mechanical wick operationalization is therefore original/speculative and has
a low prior.

## Frozen event and 96-cell grid

Use `EURUSD`, `GBPUSD`, `AUDUSD`, `NZDUSD`, `USDCHF`, and `USDCAD`. Aggregate exactly 15 consecutive
valid interval-start M1 candles into Europe/London wall-clock M15 bars. For completed signal bar
`t`, define:

- `range_t = high_t-low_t`, requiring a positive range;
- `upper_wick_ratio = (high_t-max(open_t,close_t))/range_t`;
- `lower_wick_ratio = (min(open_t,close_t)-low_t)/range_t`;
- `close_location = (2*close_t-high_t-low_t)/range_t`;
- upper rejection when upper wick ratio is at least `w` and close location is at most `-c`;
- lower rejection when lower wick ratio is at least `w` and close location is at least `c`.

Because `c>0`, upper and lower rejection are mutually exclusive. `FOLLOW_REJECTION` trades short
after upper rejection and long after lower rejection. `FAILURE` trades the opposite side.
Require `range_t/ATR96_{t-1} >= r`.

The Cartesian grid is:

- `r in {0.5,1.0}`;
- `w in {0.4,0.6}`;
- `c in {0.25,0.5}`;
- response mode in `{FOLLOW_REJECTION,FAILURE}`;
- hold in `{30,60,120}` minutes;
- stop in `{1,2} * ATR96_{t-1}`.

This is exactly `2*2*2*2*3*2 = 96` selectable cells. Signals are completed M15 closes ending
09:00 through 12:45 London and every exit is due by 15:00.

## ATR, timing, costs, and defects

True range uses the previous valid observed M15 close, including routine elapsed daily/weekend
gaps. Wilder ATR(96) seeds from the first 96 valid observed true ranges and is frozen through
`t-1`; elapsed gaps do not reset it. Signal bar `t` itself must contain exactly 15 physically
consecutive valid M1 candles.

Entry is the final M1 chart/bid close of the signal M15 bar. Its earlier path cannot trigger the
new stop. Management begins with the next M1. Stops are fixed chart/bid levels; V2 applies its
resolved or frozen-fallback spread, commission, slippage, executable trigger side, and adverse-gap
fill. Stop precedes a time exit in the same M1 bar. Any missing, duplicate, invalid, or non-finite
M1 interval in `(entry_time,due_exit_time]` fails only affected cells and must be reported.

Every cell owns isolated equity, positions, exposure, overlap decisions, and failure state. Within
a cell, same-timestamp symbol entries use one common pre-entry equity snapshot and each risks 0.25%
before costs.

## Advancement and multiplicity

For each response mode the center is `r=0.5`, `w=0.4`, `c=0.25`, hold 60, stop 1. Exact one-axis
neighbors are `r=1.0`, `w=0.6`, `c=0.5`, hold 30, hold 120, and stop 2. A mode advances only if the
center and at least three neighbors pass normal and doubled costs, both UTC-midpoint development halves,
at least three positive symbols per half, at least 300 center trades, and removal of the center's
five best London dates. Date ties sort ascending.

Uncertainty uses the eligible London-weekday daily net-R series, including zero on eligible no-
trade dates, with 10,000 circular five-date block-bootstrap resamples and seed 2026009. The normal-
cost center interval must lie wholly above zero. All 96 cells and identifiable prior I-12/I-40,
wick, no-wick, outside-bar, and key-reversal trials remain in the multiplicity ledger. Missing
history prohibits a confirmatory claim; no isolated-cell rescue or final holdout is allowed.

## Pre-review skeptical boundary

A wick does not prove rejection or order flow, OHLC cannot distinguish a genuine extreme from
spread/quote behavior, and signal-close entry may arrive after any response. The expected value is
low; the batch is useful primarily as a cheap, fully retained falsification.
