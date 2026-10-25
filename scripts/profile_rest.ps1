# Profile strategies 2-7 one after the other (strategy 1 was profiled on 2026-10-25).
# Output appended to results\profile_all2.log.
foreach ($s in 'ny_index_sweep', 'no_wick', 'trend_following', 'gap_fade', 'opening_range', 'gap_momentum') {
    & .venv\Scripts\python.exe -m backtester.tools.strategy_profile --strategy $s --workers 6 *>> results\profile_all2.log
}
"ALL DONE" | Out-File -Append -Encoding utf8 results\profile_all2.log
