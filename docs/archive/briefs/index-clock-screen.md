# Brief: two-stage calendar x clock screen on index CFDs (discover 2010-2014, confirm 2015-2021)

Pre-registered by Opus 2026-11-09 before any index pre-sample data was read; same design as
`briefs/calendar-clock-screen.md` (read it, incl. its Definitions section) with the changes below. The
user's go for the download: "Yes, download indices" (2026-11-09). Read `AGENTS.md` first; hard limits
apply (no commits, no servers, no `live/`, no `.env`, no downloads). No strategy code, grids or spec
edits. Never touch data after 2021-09-13.

## Data

1. Import `data/raw/histdata_presample/` US500, NAS100, GER40, UK100, JP225 (histdata SPXUSD, NSXUSD,
   GRXEUR, UKXGBP, JPXJPY, 2010-2014) into `data/cache/histdata_presample/` the way the FX pairs were
   (`backtester.data.histdata`, US DST clock rule through 2018). Per-year clock check like the FX one
   (`results/presample_2008_2014/clock_check_new_pairs.md`): for US500 / NAS100 the 13:30 / 14:30 UTC
   release spikes and the cash open; GER40 / UK100 / JP225 their cash opens. Exclude and name a year whose
   clock cannot be confirmed. Note `histdata.py`'s GER40 instrument-switch rule (2020-06-15).
2. Confirmation: the default cache (MT5 preferred) 2015-01-02..2021-09-13.

## Cells (fixed)

5 indices x 12 two-hour UTC blocks x the same 11 day classes = 660 cells. Rollover blocks 20-22 and 22-24
reported, never selected. Additionally never select a block in which the symbol has fewer than 60 % of
its weekdays with both endpoint closes present in discovery (exchange breaks / closed hours).

## Thresholds (same as FX)

Stage 1 (2010-2014): n >= 60, |t| >= 4.0, |mean| >= 2 x cost bp (cost from the cost model at the
symbol's median price, as `tools/time_of_day_profile`). Stage 2 (2015-2021), survivors only: same sign,
|mean| >= 1.5 x cost, t >= 2.0 in that direction, same-sign difference vs the same block on other days.

## Output

`knowledge/research/reports/2026-11-09_index_clock_screen.md` (design, clock check, coverage per block,
survivors with both stages, confirmed list, top 20 discovery cells by |t|). Report counts and the list.
