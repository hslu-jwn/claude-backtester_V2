# R-2026-007 — M15 shock-response screening batch

Status: speculative high-throughput development design; unreviewed and unqueued.  
Date: 2026-11-04

## Purpose

Test whether unusually large completed M15 returns show short-lived continuation or reversal on
six V2-supported FX pairs. This is not a new independent economic family: it is explicitly
registered under the adverse-prior I-61/R-2026-004 shock-response family. Its purpose is to test a
lower-horizon, calendar-light implementation in one fully counted batch, not to erase the earlier
failure or rescue it through relabeling.

## Evidence boundary

Zawadowski, Andor, and Kertesz (2006) find 30-60-minute reversal after causal extreme individual-
stock moves, with material spread sensitivity. Caporale and Plastun (2020) report continuation
within abnormal FX days and reversal on the following day, but omit trading costs. Neither source
establishes a modern M15 CFD edge. They motivate testing both response signs and treating zero net
expectancy as the default. The full papers and limitations were already inspected and recorded in
R-2026-004; this record reuses that evidence transparently.

## Frozen design

- Universe: the six FX pairs already exercised by the first real intake pilot: `EURUSD`,
  `GBPUSD`, `AUDUSD`, `NZDUSD`, `USDCHF`, and `USDCAD`. Excluding index CFDs avoids recreating
  the unresolved holiday/early-close calendar dependency.
- Build half-open M15 bars only from 15 consecutive, unique, valid completed M1 bars.
- Signal only from completed London-aligned M15 bars ending 09:00 through 12:45
  `Europe/London`; every declared 15-120 minute exit is due no later than 15:00 on the same date.
- Let `r_t = ln(close_t / close_{t-1})`. Robust scale is `1.4826 * MAD` of the 96 returns ending at
  `t-1`; the current return is excluded. Require finite positive scale and ATR(20).
- An event occurs when `abs(r_t) / scale >= k`, for `k` in `{2,3,4}`. Event direction is
  `sign(r_t)`. `CONTINUATION` trades that sign; `REVERSAL` trades the opposite sign.
- Enter at the completed M15 signal close, use a fixed `1` or `2` ATR(20) stop, and exit after
  `15`, `30`, `60`, or `120` minutes. One open position per symbol; overlapping signals are logged
  but cannot open another trade.
- The complete grid is `3 * 2 * 4 * 2 = 48` cells. All cells and prior I-61/R004 trials remain in
  the family-wide multiplicity history.

## Failure and advancement rules

Stored M1 timestamps are interval starts; a candle at `08:45` covers `[08:45,08:46)`, and the
London-aligned M15 bar ending `09:00` contains `[08:45,09:00)`. Signal construction requires 98
valid observed M15 closes through the current bar. Routine elapsed daily/weekend gaps do not reset
prior-only scale or ATR state; returns and true ranges across them use the previous observed close,
matching V2's documented indicator convention. The actual event bars `t-1` and `t` must be exactly
15 physical minutes apart, so a gap itself cannot become a signal. The signal fills at the final
M1 close and its earlier high/low cannot stop the new trade.
Stop evaluation begins with the next M1 candle. If a timestamp gap, duplicate, invalid
OHLC bar, or non-finite value occurs after entry and before the due exit, mark the affected
experiment failed rather than assuming stop survival or deleting the trade. Never enter when the
declared exit would be later than 15:00 London.

`entry_price` and the frozen stop are chart/bid levels. V2 applies resolved or fixed-fallback
spread, commission, and slippage separately to executable entry/exit fills; long stops trigger on
bid and short stops on executable ask under the existing engine rule. Any invalid interval in
`(entry_time, due_exit_time]`, including the due interval, fails the affected cell before exit.
Development halves split at the exact UTC midpoint of V2's fixed development interval; a close
exactly at the midpoint belongs to the first half.

The declared baseline is `k=3`, `CONTINUATION`, 60-minute hold, and 1 ATR stop. A single positive
cell cannot advance. For each response mode the center is `k=3`, 60-minute hold, 1 ATR stop; its
four neighbors are exactly `k=2/h=60`, `k=4/h=60`, `k=3/h=30`, and `k=3/h=120` at the same mode
and stop. The center and at least two neighbors must pass normal/doubled costs, both fixed temporal
halves, three supporting symbols, 200 pooled trades, and the frozen five-date removal. Date-level
uncertainty uses 10,000 circular five-date block-bootstrap resamples with seed 2026007. No final
holdout is authorized.

## Skeptical assessment

- The family already has an adverse local prior; this substantially lowers the chance of success.
- Threshold, sign, holding, and stop choices create 48 cells plus earlier family trials.
- Volatility clustering, scheduled news, and bid/ask bounce can imitate either response sign.
- Pooled trades share event dates and correlated instruments; use date-clustered uncertainty.
- A lucky development cell is rejection evidence for the search process, not a discovered edge.
