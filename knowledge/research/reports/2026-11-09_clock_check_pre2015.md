# Histdata clock check 2008-2014 (EURUSD pre-sample, 2026-11-09)

Opus, local script (`scratchpad/clock_pre.py`, not in the repo): pre-sample cache
`data/cache/histdata_presample/` imported with the current rule of `data/histdata.py`
(`histdata_to_utc`: US DST rule only for 2015-2018, the European rule otherwise). For every NFP
release (first Friday, 08:30 ET) and every scheduled FOMC statement (`timed_hold` calendar, 14:15 /
12:30 / 14:00 ET), the largest 1-minute |return| within +-90 minutes of the expected release; offset =
that candle's close time minus the expected UTC time.

| Year | Events | Most common offset (min) | Events about +60 min late |
|---|---|---|---|
| 2008 | 20 | +1 (6) | 2008-03-18 FOMC, 2008-10-29 FOMC |
| 2009 | 20 | +2 (4) | 2009-03-18 FOMC |
| 2010 | 19 | +1 (7) | 2010-03-16 FOMC, 2010-11-03 FOMC, 2010-11-05 NFP |
| 2011 | 20 | +1 (5) | 2011-03-15 FOMC, 2011-11-02 FOMC, 2011-11-04 NFP |
| 2012 | 20 | +1 (5) | 2012-03-13 FOMC, 2012-11-02 NFP |
| 2013 | 20 | +1 (8) | 2013-03-20 FOMC, 2013-10-30 FOMC |
| 2014 | 20 | +1 (11) | 2014-03-19 FOMC, 2014-10-29 FOMC |

+1 minute is correct (the release falls inside the candle that closes one minute later). **Every
event about one hour late is in a week where New York is on summer time and Europe is not** (mid-March
after the US switch; late October / early November between the European and the US end). No event
outside those weeks is an hour off; the few other outliers are holiday-moved NFP dates (e.g. 2008-07-04,
2009-07-03, released a day earlier) with no spike in the window.

**Conclusion:** histdata files for 2008-2014 follow the same US DST rule as 2015-2018 (the file clock
is New York based), not the European rule the importer assumes for years outside 2015-2018. In the
mismatch weeks (about 4-5 weeks a year) the pre-sample cache is one hour off. Fix before the F1a
pre-sample run: apply the US rule for all years up to 2018 in `histdata_to_utc`, re-import the
pre-sample, re-check (all mismatch-week events at +1). The main cache (2015 onward) is unaffected.
