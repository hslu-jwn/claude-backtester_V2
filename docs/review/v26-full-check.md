1. **P1 — Reveal state leaks into another simultaneous trade.** `src/backtester/ui/review_callbacks.py:121`  
   **Defect:** changing trades resets reveal only when the entry timestamp changes.  
   **Scenario:** reveal trade A, then select Next to trade B with the same timestamp; the reproduced result retained `revealed=True` and sent B’s exit before its Reveal button was pressed.  
   **Fix:** reset reveal whenever the selected index or complete trade identity changes.  
   **Trading rule/default:** no.

2. **P1 — Development portfolio diagnostics incorporate holdout results.** `src/backtester/tools/portfolio_candidates.py:423`  
   **Defect:** `existing_summary()` selects trial families, then collects their statistics without filtering out test periods.  
   **Scenario:** a development member’s family contains development and `research-test` records; the reproduced helper result included both daily Sharpes, `[0.1, 99]`, in the development portfolio’s deflated-Sharpe inputs. This affects diagnostics, although the combination-search daily R remains development-only.  
   **Fix:** restrict statistical inputs to validated development records; preserve any separately required trial-count accounting explicitly.  
   **Trading rule/default:** statistical interpretation requires Opus/user review.

3. **P1 — Cache repair is not idempotent when correction creates a previously absent day.** `src/backtester/data/cache_repair.py:244`  
   **Defect:** reruns merge active files with retained originals, treating newly generated spill days as original input.  
   **Scenario:** an original `2020-01-06 23:30` bar shifted +1 hour creates January 7. With both dates proven +1, the first run produced only `00:30`; the second produced `00:30` **and `01:30`**. The generated day was archived and shifted again.  
   **Fix:** persist the original input-day inventory, including absent destination days, and rebuild exclusively from that inventory.  
   **Trading rule/default:** no.

4. **P2 — Repair and download writers do not share exclusion locks.** `src/backtester/data/cache_repair.py:241`; `src/backtester/data/mt5_download.py:162`  
   **Defect:** repair’s symbol lock is unused by the downloader, so atomic day replacement does not prevent competing writers from overwriting each other.  
   **Scenario:** repair stages corrected development data; a simultaneous download replaces an affected day before or after publication. The final cache can contain the downloader’s uncorrected clock, or repair can overwrite newly downloaded data with its earlier snapshot.  
   **Fix:** use one shared symbol-level mutation lock for downloads and repairs, including original capture and publication.  
   **Trading rule/default:** no.

5. **P2 — Completed pipelines silently ignore changed research controls.** `src/backtester/tools/research_pipeline.py:282`  
   **Defect:** completed steps are reused without checking controls excluded from `grid_id()`, including `min_trades`.  
   **Scenario:** complete a grid, then increase `min_trades` enough to disqualify its chosen variant. The grid ID stays unchanged; the pipeline skips research and retains the old choice. The mocked completed pipeline invoked research zero times.  
   **Fix:** fingerprint pipeline inputs separately and invalidate affected steps when selection/report controls change, while retaining the permanent test guard.  
   **Trading rule/default:** no threshold change is needed.

6. **P2 — Repaired candle content does not invalidate cached regime attribution.** `src/backtester/tools/portfolio_candidates.py:183`  
   **Defect:** the search fingerprint records available development dates but no candle-content version.  
   **Scenario:** repair or re-import changes OHLC values while preserving filenames/dates; `search_hash()` stays unchanged, so `cached_search()` returns regime attribution calculated from the old candles.  
   **Fix:** include a cache-generation identifier or relevant development-file fingerprints in the search identity.  
   **Trading rule/default:** no.

7. **Specification conflict requiring a user decision — Default costs can use holdout observations in development.** `src/backtester/engine/costs.py:329`; `src/backtester/engine/spread_table.py:61`  
   **Issue:** the default measured spread table permits future-year fallback and whole-year calibration.  
   **Scenario:** NAS100 has table years 2021–2026; a January 2020 development fill uses its nearest 2021 observation. The reproduced default spread was `0.6`. Whole-year 2021 calibration also crosses the September 14 cutoff.  
   **Suggested resolution:** Opus should ask the user whether retrospective cost calibration is an explicit exception, or whether calibration must use development-only/prior observations.  
   **Trading rule/default:** **yes—list for the user only.** `risk-management.md:109` explicitly mandates this default, while AGENTS.md prohibits future information. I have not guessed a replacement rule.

“Checked, looks fine”: portfolio member loading validates development dates and trade timestamps; holdout attempts have a permanent reservation in the default location. Normal unrevealed chart payloads clamp candles and suppress exits. News schedule objects exclude actual/forecast/previous values, and the engine’s tested blackout behavior follows the documented acceptance-time convention. JSON and Parquet writers use unique temporary files and atomic replacement with bounded Windows sharing retries. The exercised tick-rounding cases passed.

Short duplication list: queue/cache modules duplicate permission-retry plumbing; pipeline/UI modules duplicate Monte Carlo directory naming. These are maintenance observations.

**Report:** reviewed the scoped code read-only; changed no files. **73 existing test cases passed** through direct invocation without pytest’s filesystem fixtures; targeted in-memory reproductions confirmed the defects described above. Full pytest, browser checks and real process-concurrency tests were not run. Concurrent workspace edits were observed during review. Open question: the cost-calibration exception in finding 7.