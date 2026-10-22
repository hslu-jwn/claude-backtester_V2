| # | severity | category | file:line | finding | evidence | fix | changes results? |
|---|---|---|---|---|---|---|---|
| 1 | high | correctness | [series.py:103](X:/Dokumente/Projekte/backtester-claude/backtester-claude_V2/src/backtester/core/series.py:103) | Negative `window()` stops expose future candles. | With five candles and cursor 0, `window(0, -1)` returns candles 0–3. Appending future candles changes the returned window. | Reject negative stops before slicing; add regression coverage. | unknown |
| 2 | medium | correctness | [models.py:49](X:/Dokumente/Projekte/backtester-claude/backtester-claude_V2/src/backtester/core/models.py:49) | OHLC validation accepts NaN and infinity. | Reproduced acceptance of NaN in each OHLC field; all-infinite OHLC passes and produces `range = NaN`. | Require finite OHLC values before checking their ordering. | unknown |
| 3 | medium | correctness | [models.py:49](X:/Dokumente/Projekte/backtester-claude/backtester-claude_V2/src/backtester/core/models.py:49) | Naive timestamps enter storage despite the UTC contract. | A naive candle constructs successfully; `HigherTimeframeClock.view_at()` with UTC `now` then raises `TypeError`. | Reject naive timestamps and normalize aware timestamps to UTC at ingestion. | unknown |

Reviewed all five core files, architecture/replay rules and calendar timestamp conventions; tests reside in `tests/test_core_*.py`, not `tests/core/`.  
Verified HTF close boundaries, gaps, empty clocks, duplicate/reversed timestamps, frozen candles and valid-view future-append invariance.  
Audit 13.6–13.23: none directly targets `core/`; findings in other modules remain unverified here.  
Tests: **7 passed**, using original candle fixtures with caches disabled and the disk-writing autouse fixture omitted; additional snippets confirmed the findings. Golden impact unverified.  
Report: read-only review completed; files changed: **none**; open questions: **none**.