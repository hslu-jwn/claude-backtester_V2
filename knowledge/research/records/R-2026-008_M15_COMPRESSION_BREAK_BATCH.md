# R-2026-008 — M15 compression-break response batch

Status: speculative high-throughput development design; unreviewed and unqueued.  
Date: 2026-11-05

## Purpose and prior

Test whether a completed close outside a causally frozen low-range M15 block continues or fails.
This is the compression/breakout family already mapped under I-32/I-33, not a new independent
economic discovery. The prior is adverse: the bounded evidence review found no direct cost-aware
intraday study, nearby opening-range tests were broadly negative, and the closest registered daily
squeeze study reported no volatility burst and a losing squeeze-breakout rule.

The fast-lane mandate permits a transparent speculative falsification batch despite this prior. It
does not permit relabeling a favorable cell as confirmation or reopening the failed opening family.

## Evidence boundary

- Holmberg, Lönnbark, and Lundström (2013) report crude-oil opening-range breakout profitability;
  the event is the market open, not a preceding compression block.
- Magner, Sanhueza, and Lavín (2026) find long-horizon equity breakouts load on momentum without
  significant factor-adjusted alpha; the horizon and universe do not transfer.
- Girgin (2026, SSRN) reports that daily Bollinger/TTM squeezes do not precede volatility bursts
  and that the squeeze-breakout strategy loses. It is not peer reviewed but is direct adverse
  context.

These sources motivate falsification and limitations, not a profitability claim.

## Frozen event and 72-cell grid

Use the six previously exercised FX pairs: `EURUSD`, `GBPUSD`, `AUDUSD`, `NZDUSD`, `USDCHF`, and
`USDCAD`. Stored M1 timestamps are interval starts; aggregate exactly 15 valid consecutive candles
into Europe/London wall-clock M15 buckets.

At signal bar `t`, all features use completed bars only:

- `ATR96_{t-1}` is Wilder ATR(96), excluding `t`.
- For `L in {4,8,16}`, freeze the prior block `t-L ... t-1`, its highest high, lowest low, and
  median true range.
- The block is compressed when `median(TR block) / ATR96_{t-1} <= c`, for `c in {0.50,0.75}`.
- An up break requires `close_t > prior_block_high`; a down break requires
  `close_t < prior_block_low`. Wick-only breaks do not qualify.
- `CONTINUATION` trades the break direction; `REVERSAL` trades the opposite direction.
- Hold for `{30,60,120}` minutes with a fixed `{1,2} * ATR96_{t-1}` chart/bid stop.

The exact grid is `3 * 2 * 2 * 3 * 2 = 72` cells. Signal closes range from 09:00 through 12:45
London, with every due exit no later than 15:00. One position per symbol per cell; an open position
does not suppress signals or state in other cells.

True range is `max(high-low, abs(high-previous_observed_close),
abs(low-previous_observed_close))`; routine elapsed daily/weekend gaps remain represented. ATR96
seeds with the arithmetic mean of the first 96 valid observed TRs, then uses Wilder's recurrence.
The full event window `t-L ... t` must nevertheless be physically contiguous at 15-minute spacing,
so a gap itself cannot form a compression block or breakout signal.
Even-length block medians average the two middle sorted TRs. Every cell owns an isolated virtual
portfolio; no equity, exposure, position, overlap, or failure state crosses cells.

## Timing, costs, and defects

The signal fills at the final M1 close of the completed M15 bar. The entry candle's earlier path
cannot trigger the new stop; management begins with the next M1. Stops are chart/bid levels while
V2 applies resolved or frozen-fallback spread, commission, and slippage to executable fills.
Long stops trigger on bid, short stops on executable ask, and adverse gaps use V2's worse
executable opening fill. Stop precedes time exit in the same M1 bar.

Pre-entry elapsed market gaps do not reset the observed-sequence ATR warm-up, but any gap inside
the complete `t-L ... t` event window suppresses that signal. Any missing, duplicate, invalid, or
non-finite M1 interval in `(entry_time,due_exit_time]` fails only the affected cell and must be
reported; it may not erase the trade or imply stop survival.

## Advancement and multiplicity

For each response mode the center is `L=8`, `c=0.75`, 60-minute hold, and 1 ATR stop. Its exact
neighbors are `L=4`, `L=16`, `c=0.50`, hold 30, and hold 120, changing one axis only while keeping
other center settings. A mode advances only if the center and at least two of these five neighbors
pass all gates: positive normal and doubled-cost net R, both UTC-midpoint development halves,
positive center net R in each half for at least three symbols, at least 300 pooled center trades,
and positive results after the center's five best London dates are removed from it and its
neighbors under both normal and doubled costs. Ties use ascending date.

Date uncertainty uses an eligible-weekday series with zero on no-trade dates and 10,000 circular
five-date block-bootstrap resamples, seed 2026008. The normal-cost center interval must be wholly
positive; neighbor intervals are diagnostic. Exactly two isolated, non-selectable plain-break
rows—both response modes at `L=8`, hold 60, stop 1—report incremental mean daily net R and cannot
alter advancement. Count 72 cells, both diagnostics, and every identifiable prior compression/
opening-breakout trial; an incomplete historical ledger prohibits a confirmatory claim. No final
holdout is authorized.

## Skeptical verdict

Expected value is low. Compression can describe volatility state without predicting direction;
the signal may merely buy after movement, and reversals may be bid/ask or liquidity effects. The
batch is useful if it cheaply rejects both signs while preserving every cell and the adverse prior.
