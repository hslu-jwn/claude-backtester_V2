# Brief: V2.6 step 2 — data fixes 13.12-13.16, 13.18 + small items

Context: ROADMAP › V2.6 build order step 2 (accepted by the user 2026-10-26); items in
`docs/archive/ROADMAP-v1.md` › Phase 13 (13.12-13.16, 13.18 and its "Minor" list); data
sources in `docs/ARCHITECTURE.md` › Data sources and `data/sources.py` (MT5 preferred day by
day, rule of the user 2026-10-19). Decisions of the user, 2026-10-26, below. Correct data
first; nothing here changes a trading rule.

## Items

1. **13.12 histdata clock 2015-2018.** `data/histdata.py:histdata_to_utc` assumes "NY standard
   time + Europe DST" for every year; in 2015-2018 the files follow US DST, so the weeks
   between the US and EU DST changes (mid-March, end Oct / early Nov) are 1 h late. Make the
   rule date-dependent. **Prove the rule with data before coding it**: measure per year and DST
   gap week with an anchor that does not depend on another possibly-wrong feed (e.g. the FX
   weekly open Sunday 17:00 New York, the index cash open 09:30 New York volume / range jump,
   the gold daily break), and also with `tools/mt5_clock_check.py` / `mt5_compare.weekly_offsets`
   where MT5 2020+ overlaps. Write the evidence table to `results/clock_check_histdata.md`.
   Tests: the conversion in every DST gap week 2015-2019 and a normal week each year.
2. **13.14 MT5 before 2020 (decision: fix the clock + drop bad days).** The server clock rule
   `America/New_York + 7 h` holds only from 2020; before, 1 h shifts in US-only DST weeks
   2015-2019 and most Fridays 2010-2014 (V1 audit). Correct the clock per date **where the
   shift is proven** (same evidence method as 1, plus histdata where both exist; table in
   `results/clock_check_mt5.md`); where a period's offset cannot be proven, do not guess: list
   it and drop those MT5 days from the preferred source so histdata (if any) fills them.
   Sparse / empty days (XAUUSD / XAGUSD 2010-12 ~21 bars, GBPUSD Jan 2019, 23 empty US30 days
   2019): a day with far fewer bars than its symbol's normal weekday (threshold as a setting,
   default < 50 % of the median weekday bar count of that symbol and year) counts as missing,
   not valid, so histdata fills it. The "prefer MT5" rule stays.
3. **13.13 GER40 histdata (decision: drop).** From 2020-06-15 the GER40 histdata files are
   Euro Stoxx (GRXEUR, ~3,100 instead of ~11,960). Drop those days from the GER40 histdata
   cache. Add a **price-continuity check** to the histdata importer: a jump between
   consecutive days' closes beyond a threshold (setting; e.g. > 25 % without a weekend /
   holiday explanation) stops the import of that file with a clear message naming file and
   date. Test with a synthetic file.
4. **13.15 one-day holes on 1 January** (XAUUSD / GBPUSD / GBPJPY 2020, NAS100 / US500 2018,
   15 symbols 2021): year-by-year imports drop the day that spans two files. Import
   neighbouring years together (or carry the boundary day over) and count bars from both
   files. Test with two synthetic year files.
5. **13.16 MT5 downloader swallows errors:** only the specific "no history before X" result
   may count as "before history"; any other `Mt5Error` in the first chunk is an error
   (non-zero exit, message); a wrong broker / symbol name must not report "no new days" as
   success. Tests with the fake MT5 (`tests/live/fake_mt5` or the data tests' fake).
6. **13.18 output folders:** grid parts without `--out` must not overwrite each other (any
   tool left with `--part`; the old `orb_grid` / `gap_fade_grid` were merged into the research
   runner, check what remains); the Monte Carlo output folder name includes `--source`,
   `--seed`, `--runs`. (The Windows PermissionError / shared `.tmp` part was fixed in V2.6a:
   `filelock.py`, unique temp names; reuse that.)
7. **Small items (decision: same step):** `mt5_download --end` rejects today / future;
   Binance day holes are retried once; clean errors instead of tracebacks for `show` (end <=
   start, bad `--tz`) and `trials add --count -1`; `spread_table.py` reuses the MT5 defaults
   instead of duplicating them; `check.py` reads one year at a time instead of whole
   histories; `.gitignore`: put comments on their own line and ignore the stray hook file
   `C:Usersjusti.claudeclaude-notify-signalsstop` (delete the file if it exists in the repo
   root); remove `.vscode/` (if untracked leftovers) and `data/cache/dukascopy/` leftovers
   only if empty or clearly unused (list what you removed); add numpy / requests to the
   `data` extra in `pyproject.toml`.

## Re-import (do NOT run it yourself)

The cache rebuild is long. Write it as queue jobs: a script / command list
`scripts/rebuild_cache_v26b.md` (or a `--plan` option) with one `python -m backtester.tools.queue
add -- ...` line per symbol (histdata re-import with the new clock and continuity check, MT5
cache correction / bad-day marking), so Opus queues and runs them afterwards. Code must be
able to fix the existing cache in place or rebuild it from `data/raw/` (raw files stay
untouched). Opus runs the rebuild, the data check report (`tools/check.py`) and the golden
check afterwards.

## Answers given up front (Opus, 2026-10-26)

- UTC everywhere, `zoneinfo` for the rules, never hard-coded offsets (AGENTS.md › Time); a
  date-dependent rule is a small table of periods with its evidence, documented in
  `docs/ARCHITECTURE.md` › Data sources in the same change.
- The golden lists (2023) should not change (2023 is outside every fixed period); if they
  do, stop and report why.
- Development-period results (2015-2021) will change; that is expected, report nothing
  beyond the data check.
- No new dependencies; no network in tests; never run the MT5 terminal or a download in tests.

## Rules

AGENTS.md (never commit / push / branch; no lingering processes; never edit
`src/backtester/live/`; no credentials). Test-case list first (`briefs/v26b-test-cases.md`),
then tests, then code. Run only the tests you touched (`pytest -q tests/data tests/tools >
results\pytest_v26b.log 2>&1` plus any other folder you changed). The evidence measurements
(items 1-2) may read the existing caches; keep each under ~10 minutes and write a log.
Report: files changed, test results, the evidence tables' conclusions (which periods are
proven, which are dropped), what you removed (item 7), open questions.
