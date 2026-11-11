# Brief: screen the FX fixing "W" pattern (Krohn, Mueller, Whelan, JF 2024) on development data

Read `AGENTS.md` first; hard limits apply (no commits, no servers, no `live/`, no `.env`). Analysis task:
no strategy code, no grids, no spec changes. Development data only (before 2021-09-14).

## Source (verified by Opus from the Bank of Canada summary, SWP 2021-48 / JF 79(1) 2024 541-578)

"the US dollar, on average, appreciates in the hours before fixes and depreciates after fixes"; 5-minute
spot returns, nine currencies vs USD; Tokyo fix (09:55 JST), Frankfurt / ECB (14:15 CET) and London
(16:00 London WMR) give a W-shaped 24-hour pattern; mechanism: dealers hedge an unconditional USD demand
at the fixes.

## Already tested here (do not re-propose): F1a (EUR falls 07:00-13:00 London; failed pre-sample),
FX_LONDON_FIX_REV (post-London-fix reversal; rejected 2026-10-29), Gotobi G1 (USDJPY into the Tokyo fix
on gotobi days; passed; the all-days version loses: -62 R pooled over 3,436 trades at a 1-ATR stop).

## Task

1. With `python -m backtester.tools.time_of_day_profile` (and small scratch scripts in `results/` only if
   needed, using the existing loaders), measure for EURUSD, GBPUSD, USDJPY, AUDUSD, NZDUSD, USDCAD, USDCHF,
   2015-01-02..2021-09-13, the mean USD-signed return (bp, positive = USD up) in these windows, all
   weekdays and month-end days separately: Tokyo pre-fix 07:55-09:55 JST and post-fix 09:55-11:55 JST;
   ECB pre-fix 12:15-14:15 CET and post 14:15-16:15 CET; London pre-fix 14:00-16:00 London and post
   16:00-18:00 London. Report also the modeled round-trip cost in bp per symbol (from the tool) and a
   t-statistic (day-clustered) per window.
2. Verdict per window: does the mean clear 1.5 x the round-trip cost with |t| >= 3? A window that does is
   a candidate for a pre-registered hypothesis (Opus decides); one that does not is screened out.

## Output

`knowledge/research/reports/2026-11-09_fix_w_pattern_screen.md`: method, a table (window x symbol: mean
bp, t, cost bp, verdict), and 3-5 lines of conclusion. Report the file and the verdicts.
