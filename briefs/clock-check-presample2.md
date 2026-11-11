# Brief: per-year clock check of the new pre-sample histdata (XAUUSD, XAGUSD, USDCAD, USOIL, UKOIL)

Read `AGENTS.md`; hard limits apply (no commits, no servers, no `live/`, no `.env`, no downloads). Analysis only:
write only results files and the report below; no code changes.

The files were imported 2026-11-10 into `data/cache/histdata_presample/` (gold from 2009-03, silver 2009-05,
USDCAD 2008, USOIL / UKOIL 2010-11, all to 2014). Check each year's clock the way the earlier pre-sample checks
did (`results/presample_2008_2014/clock_check_new_pairs.md` and its csv: release spikes at US NFP 08:30 New
York and FOMC 14:00 New York; for oil also the EIA report Wednesday 10:30 New York). Name any year whose clock
cannot be confirmed (it is excluded from pre-sample checks). Write
`results/presample_2008_2014/clock_check_metals_cad_oil.md` (+ csv). Report per symbol and year: confirmed /
offset / not enough events.
