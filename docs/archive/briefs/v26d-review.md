# Review: V2.6d work of 2026-10-27 (read-only)

Review the commits `da7efb9..HEAD` on branch v2-6-research (`git log --oneline da7efb9..HEAD`,
`git diff da7efb9..HEAD -- . ':!tests/golden'`). Most of it was written by Claude Sonnet
subagents and reviewed only by Opus; you are the cross-review (AGENTS.md › Team). Read-only:
change no file.

Focus on correctness bugs, in this order:
1. `engine/costs.py`, `engine/trade.py`, `engine/backtest.py`, `analytics/records.py`, `runner.py`:
   the new FTMO currency conversion adjustment (`conversion_r` = -0.7 % x sum(share x |gross R|)
   for a non-USD profit currency) and the NATGAS / DXY commission. Is it charged exactly once per
   trade, also with partial closes, break-even, stop-and-reverse and open trades at the end of
   data? Is it in net R everywhere net R is rebuilt (daily R, portfolio scaling, entry screen,
   Monte Carlo, results page)? Old trades CSVs load as 0?
2. `data/news.py` `matching_events` (an impact with a 0 / 0 window is ignored entirely) and
   `tools/news_clean.py` (rule 1: suspicious 00:00 / 23:59:59 Asia/Tehran rows -> day-only on
   the local date; rule 2: release time imputed from >= 3 siblings of the same event, currency
   and country, mode local time >= 60 %, DST-correct UTC). Any wrong date, time zone or sibling
   selection?
3. `tools/research.py`: DSR and family Sharpes now on daily net R like the trial log; resume
   re-runs old per-trade scorecards. Same period bounds as the trial log? Any place still mixing
   per-trade and daily values?
4. `live/bot.py` (`BOT_STRATEGIES`, `parse_config`, `--strategy fill_probe`) and
   `strategy/fill_probe/`: can the probe or the forward-test default misbehave live (state after
   restart, stale signals, comment prefixes, risk defaults)? Report only; you may not edit live/.
5. `ui/pages/chart.py` + `ui/assets/chart.js` live refresh, `presets.py` / `run.py`,
   `jobs/temperature.py`, `tools/fill_report.py` (sign conventions of slippage), `ui/assets/theme.js`.

For each finding: file:line, what is wrong, a concrete failing input, severity (bug / risk / nit),
and the smallest fix. Skip style. If something is fine, say so in one line per area. Keep the
answer under 900 words.
