# Gotobi test: M1 integrity diagnostic, 2026-11-09

This is an inspection of existing trades and cached candles, not a strategy run or retest. The one-time G1 result remains **not confirmed**. Counts below concern the 321 saved USDJPY trades in `results/20261109-215845_USDJPY-EURJPY/`; timestamps are UTC and gap lengths count missing M1 candle opens, including both listed ends. The check covers each trade from entry time through one minute before exit, including longer holiday holds and shortened stop-outs.

## Cause and source evidence

The 302 tolerant / 303 strict scratch flags are predominantly a **source reconstruction error**. `settings.json` records `cache_dirs` as histdata, but `runner.write_results` serializes only `sources.cache_dir`, omitting preferred and fallback directories. `research.main` ordinarily uses `DEFAULT_SOURCES`, which prefers MT5 per UTC day; `timed_hold_gates` reconstructs `SymbolSources` from `cache_dirs` alone. The saved settings do not by themselves prove the original source configuration, but the following comparisons strongly identify MT5 as the trade feed:

| Comparison using current cache | Histdata only | MT5 only | Default preferred mix |
|---|---:|---:|---:|
| Strict failures | 303 | 313 | 313 |
| Tolerant failures | 302 | 209 | 209 |
| Entry candle present / entry close equals recorded entry | 19 / 7 | 321 / 321 | 321 / 321 |
| Exit candle present / exit close equals recorded exit price | 19 / 4 | 321 / 319 | 321 / 319 |

The two MT5 exit differences are the two stop-loss exits, where the recorded stop price need not equal the candle close. The current preferred and MT5 M1 streams have the same 1,902,877 bars over 2021-09-14 through 2026-11-09 inclusive. This and endpoint matches are strong evidence, not a historical cache fingerprint: files could have changed since the run, and saved results do not contain every candle used by the engine. The current histdata-only check has 302 missing exit candles, including all 62 trades per year in 2022–2025 and 54 in 2026. Most 2022–2026 histdata trade windows contain no bars at all; two Christmas holds span 1,686 missing minutes. The single remaining strict histdata flag is a seven-minute gap starting 2021-12-09 22:03; it is tolerated.

The loader's inclusive UTC day selection was checked through 2026-11-09, one day beyond the run end: the latest recorded USDJPY exit is 2026-11-05 00:55 UTC. Thus truncation at the requested test end does not explain these flags. The code uses candle-open timestamps and the integrity check correctly tests through `exit_time - 1 minute`; observed endpoint matches support that convention.

## Actual MT5 gaps

The table lists gaps longer than five minutes **within the saved trade windows**, grouped by trade entry year. Counts are gaps, not necessarily distinct trades; a hold can contain more than one. Typical entries are missing-open start time and length. These are current-cache observations, not an assertion that every missing bar represents lost ticks.

| Year | Gaps >5 min | Most frequent start and length (count) | Tolerant flagged trades |
|---|---:|---|---:|
| 2021 | 12 | 21:55, 10 min (6); 20:55, 10 min (4) | 5 |
| 2022 | 65 | 20:55, 10 min (21); 21:55, 10 min (16); 20:55, 12 min (7) | 40 |
| 2023 | 63 | 20:55, 10 min (23); 21:55, 10 min (14); 20:55, 11 min (8) | 40 |
| 2024 | 64 | 20:55, 10 min (38); 21:55, 10 min (16) | 40 |
| 2025 | 67 | 20:55, 10 min (38); 21:55, 10 min (18) | 43 |
| 2026 | 58 | 20:55, 10 min (34); 21:55, 10 min (13) | 41 |

For example, 2021-09-14 is missing 20:55–21:04 (10 minutes). The one-hour seasonal shift is consistent with New York DST around the 17:00 New York rollover, not a UTC timestamp shift in the whole series. Of 209 tolerant flags, 206 include a gap starting at 20:55; another starts at 20:54 on 2022-05-30. Two are Christmas closures: 2024-12-24 21:52 for 1,453 minutes and 2025-12-24 21:55 for 1,450 minutes. Flagged entries fall Monday–Thursday New York time, not just at weekends. All 321 MT5 exit candles exist and all checked candles pass the OHLC validity predicate.

The literal registered tolerance permits rollover gaps only within **21:00–23:00 UTC**, so a 20:55 start correctly fails that written condition, even when it straddles the 17:00 New York rollover. The 21:55 ten-minute gaps fall inside the permitted interval. This seasonal boundary is a mismatch between the stated UTC window and actual observed rollover timing, not evidence that the implementation violated the written rule. The two long Christmas closures also extend outside that interval and are properly flagged. Do not silently redefine or retroactively relax the registered gate.

## Effect and proposal

The 302 histdata-only flags do not show that the engine lacked those candles: matching entry and exit prices show it almost certainly used MT5 candles the scratch loader omitted. Genuine missing MT5 intervals still matter: an unobserved price excursion could have reached a stop, and sparse bars near rollover can affect recorded execution and risk. The two long closures also leave a substantial unobserved period. Endpoint agreement cannot reconstruct missing prices or quantify the possible change in net R. Therefore +6.6 R and the reported significance are the saved backtest outcomes, not independently verified outcomes under complete price history; no revised result or confirmation claim follows from this diagnostic.

For future runs, serialize main, preferred and fallback source mappings and an immutable dataset fingerprint, and reconstruct precisely that source configuration in integrity tools; legacy settings should explicitly report that their original preferred source is unknown rather than assume the main cache was the whole feed. Add tests for preferred-day selection, absent files, range boundaries, 20:55 and 21:55 UTC rollover, and multi-day holidays before any shared-code change. If a future study wants a DST-aware rollover tolerance, specify and approve it prospectively, with its exact allowed interval and holiday treatment; the current fixed-UTC rule should remain reported as registered. No code or trading specification was changed here.
