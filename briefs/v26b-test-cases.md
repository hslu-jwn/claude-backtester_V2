# V2.6b test cases (written before implementation)

All tests are offline; fixtures use synthetic bars and temporary caches. No terminal,
download, golden run, or production cache rebuild is run by Codex.

1. Clock evidence: measure Sunday FX opens and gold daily breaks per year, including
   every US/EU DST gap week in 2015–2019 and normal weeks. Compare cached overlapping
   feeds with `weekly_offsets` in 2020+. Record absent/contradictory evidence explicitly.
   Only proven periods receive a conversion; uncertain pre-2020 MT5 days are excluded.
2. Histdata conversion: all gap weeks and a normal week per year 2015–2019; mixed-year
   input; transition skipped/repeated times rejected; 2023 conversion unchanged.
3. MT5 quality: empty/sparse weekdays below 50% of symbol/year median rejected;
   equality accepted; configurable threshold; normal weekends retained; rejection
   falls back to histdata; uncertain clock days excluded; repeat repair is idempotent.
4. Histdata GER40: exclude UTC days from 2020-06-15; keep last valid day; do not modify raw
   files. Synthetic >25% day-close discontinuity names file/date and writes nothing;
   configurable threshold and explicitly explained date exemptions.
5. Boundary: two synthetic adjacent yearly files contribute both halves of January 1;
   separated periods never claim full coverage of a partial day.
6. MT5 download: only explicit no-history result is skipped before history; symbol,
   connection and other first-chunk errors propagate; errors after first bars propagate;
   today/future end and reversed range rejected before session or writes.
7. Binance: missing daily archive retried once, recovery succeeds, persistent hole
   reported; cached days skipped; checksum/network failures remain errors.
8. CLI: show reversed/equal range and invalid timezone produce clean nonzero errors;
   trials negative count rejected before log write; spread tool shares MT5 defaults.
9. Output paths: enumerate remaining --part users; default paths distinct across parts;
   Monte Carlo defaults distinguish source, seed and runs, explicit --out preserved.
10. Check tool: read one year at a time, preserve cross-year gaps and aggregate report.
11. Queue plan: one histdata job per symbol imports neighbouring years together; one
    MT5 repair job per symbol; jobs accepted by queue whitelist; no rebuild executed.
12. Packaging/cleanup: data extra includes existing numpy/requests dependencies;
    ignore comments on separate lines; remove only named stray file and untracked,
    empty/clearly unused leftovers, logging actual removals.

## Addendum A-C regressions (2026-10-26; before implementation)

- A reference symbol proves a date's residual shift; MT5-only US30 inherits it.
- Opposing reference readings make the server date ambiguous; retain both readings,
  exclude the date for every symbol, and count it separately from no-reference dates.
- No decisive reference excludes a development date, including dates in 2020/2021.
- Development ends on 2021-09-13 inclusive; 2021-09-14 and 2023 retain timestamps/bytes.
- Sparse reference days cannot prove a clock; per-symbol density filtering remains.
- Repair order and reruns use original reference files and the same frozen server table.
- Year-boundary re-bucketing remains covered by the existing regression.
