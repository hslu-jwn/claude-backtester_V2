# UI redesign proposal (look and clarity only, content stays)

**Decisions (rule set by the user, 2026-10-23; items marked "Opus" were left to Opus):**
dark only, no light switch; Monte Carlo and prop-firm pass only for the chosen variant of a
research run; the grey Risk tab is merged into Backtest; the one-line idea is a field in the
grid file (`idea = "..."`), written from the spec's source (Opus); best regime and parameter
stability show "–" until V2.6 computes them (Opus); Backtest run form and Strategy move to
tabs below the chart (Opus). The tables below are the accepted list.

Reference: `docs/design/app-v2.png` (dark terminal, top tabs, key-number strip above a big chart, side panel, tabs below the chart, green/red accents). Code read: `ui/app.py`, `nav.py`, `pages/{chart,backtest,results,research,live,risk}.py`, `chart_side.py`, `settings_panel.py`, `trading_panel.py`, `prop_firm_card.py`, `research_model.py`, `tools/research.py`, `analytics/scorecard.py`.

## Summary (10 lines)
1. One dark theme for all pages (today: Chart/Results are light with a dark nav, Research/Live partly dark). Tokens: bg, panel, line, text, muted, green (up/profit), red (down/loss), amber (warning flag only).
2. Same page skeleton everywhere: top tab bar, then a compact key-number strip, then main area (chart or list), side panel on the right, tabs below the main area.
3. Rule: a number or control is **Essential** only if you look at it every visit; the rest goes behind one collapsible "Details" per card (native `html.Details`, closed by default).
4. Long explanatory sentences become a one-line sub-label or an info tooltip (`title`/dcc tooltip on a small "i"). About 20 such texts today (Monte Carlo how-text, settings notes, live notes, hints).
5. Chart page: toolbar shrinks to symbol, timeframe, 3 icon popovers; Backtest-result and Trades-in-view move to the side panel, tabs below the chart hold Trades / Overlays / Backtest.
6. Results page: key strip (Net R, Trades, Win rate, PF, Max DD, Prop pass %), equity curve large, side panel = Prop firm card, tabs below = Trades / Performance / Overview details.
7. Research page: ONE vertical list of compact cards, no horizontal scroll, click expands (details below). The table columns Half 1/2, costs x1.5, w/o best move into the expanded card.
8. Live page: strip (Balance, Equity, Today, FTMO limits, Heartbeat), big "Recent trades" chart, side = Setup in progress, tabs = Open positions / Closed / Signals / Event log / Settings.
9. Settings (strategy settings modal, MT5/Telegram connection) stay as modals/folds, only restyled; nothing removed.
10. New data needed only for the Research card: idea line, MC fields, best regime, parameter stability (see section Research). Everything else exists today.

## Top navigation tabs (proposal)
`Chart | Backtest | Research | Portfolio (later, V2.7) | Live | Settings`
- Chart, Backtest, Research, Live exist today. "Risk" is a greyed stub today (`nav.py`, `pages/risk.py` empty): keep it greyed as "Risk" until built, or fold it into Backtest results (prop firm card already lives there). Right side of bar: bot status chip (today "Bot not running", green/red dot), Update data button (today in the chart toolbar), settings gear (opens the MT5/Telegram connection, today inside Live > Settings fold and Strategy settings modal on Chart).
- Brand text "BACKTESTER" stays as plain text, no logo.

## Global elements
| element | today (where) | proposal | new place |
|---|---|---|---|
| Top bar BACKTESTER, Chart, Backtest, Research, Risk, Live, status text | `nav.py` | Essential, restyle dark; status becomes a small dot + short text; Live turns red while the bot runs (kept) | top bar |
| "⟳ Update data" + status line | chart toolbar (`update_button.py`) | Essential action, icon button; status line as tooltip, shown only while running | top bar right |
| "← Chart" link | Backtest, Results | Remove (the top tab does it) | n/a |
| Run selector dropdown "Open a run" | Results toolbar | Essential | breadcrumb row above strip |
| Hints/empty texts ("Click a row to open its results...", "Click a trade to open it on the chart...") | Research `HINT`, Results trade list | Shorten to a one-line muted hint or tooltip | under title |

## Page: Chart (`/`, `pages/chart.py`, `chart_side.py`)
| element | today (where) | proposal | new place |
|---|---|---|---|
| Symbol dropdown, timeframe buttons | toolbar | Essential | chart header row (like "GOLD · 1h") |
| Chart (candles, UTC label) | main | Essential, larger, dark | main |
| Key strip: Last price/OHLC, Net R, Win rate, Trades, Max drawdown of newest run | Backtest result card in side panel (`result_body`) | Essential, moved up as numbers strip | strip above chart |
| "Results →" link | Backtest result card | Essential (link on strip) | strip right |
| Run id of the newest run | Backtest result card | Details | tooltip on strip |
| "No backtest yet" | card | Shorten (strip shows dashes) | strip |
| Trades in view list (LONG/SHORT badge, date · setup, result R or "open", "+N more: zoom in", "No trades in view") | side panel card | Essential | side panel (right of chart) |
| Settings popover > Chart Settings: Session lines, Daily/weekly candles (Day from ...), 4h candles, Detector settings (FVG, OB strong-move filter) | toolbar popover | Session lines essential (icon toggle); the other three Details | gear popover > Details |
| Liquidity sweep (temporary): Same-height high counts, Breakout filter, Highs/lows that count, "BOS must break structure from before the top" | popover | Details | gear popover > Details |
| Note "Tolerance in ATR of the shown timeframe..." | popover | Shorten to tooltip | on the sweep group |
| Chart Overlays: Show overlays, overlay type switches, "Overlay types" note | popover | Essential master switch; type switches Details | tab "Overlays" below chart (or popover) |
| Strategy popover: strategy dropdown, "Settings…", note "Used by the Trades overlay and the backtest." | popover | Dropdown essential; note removed | tab "Strategy" below chart or toolbar popover |
| Strategy settings modal (groups Entry, Windows, Confluences, Stop loss, Take profit, Session zones, Sessions & filters, Cash session, Gap filter, Exit, Detectors, Costs, Backtest; per-field reset; Save, Save as, Rename, Delete, preset name field, Reset all to defaults, Close) | `settings_panel.py` | Keep all; each group a collapsible section, first group open, rest closed; per-field notes as tooltips | modal (dark) |
| Backtest popover: Symbols, Days (UTC), Settings preset, preset note, Run, status | toolbar popover | Essential (Symbols, Days, Preset, Run); preset note and status shortened | tab "Backtest" below chart (run form) |
| Bar replay: toggle, Select bar, start/back/play/forward, speed, exit | toolbar + replay bar | Essential as icons (replay bar only while active, unchanged) | chart header icons |
| Zoom, reset zoom | toolbar icons | Essential icons | chart left tool column |
| Picture: save PNG, Download PNG, Copy to clipboard | camera + caret popover | Details (one camera button, menu stays) | chart header right |
| Go to UTC date/time input, message/notes, order chip with "x", "UTC" | bottom bar | Go-to essential (compact); message/notes shorten; chip stays | thin bar under chart |
| Tabs below chart (new) | n/a | Trades (list of the newest run's trades), Overlays, Backtest, Strategy | below chart |

## Page: Backtest (`/backtest`, `pages/backtest.py`)
| element | today (where) | proposal | new place |
|---|---|---|---|
| Title "Backtest running / done / failed / cancelled" | card | Essential, as small status chip | strip |
| Strategy name; metas Symbols, Days (UTC), Preset | card | Essential (one muted line) | strip |
| Progress bar + percent | card | Essential | main, large |
| Detail line (candles done of total) | card | Details | under bar, muted |
| Elapsed, Time left (ETA) | stat blocks | Essential (two numbers in the strip) | strip |
| Message line | card | Essential only on error | under bar |
| "Cancel backtest" / "Cancelling …" button | card | Essential | strip right |
| "← Chart" link | card | Remove | n/a |
| Toast "Backtest cancelled. Nothing was saved." | list view | Shorten: "Cancelled" | toast |
| Previous backtests list: Date, Strategy, Symbols, Days (UTC), Trades, Net R (row opens results) | list view | Essential as compact rows (net R green/red); Days (UTC) column Details | main list |
| Title "Backtests", sub "Click a run to open its results.", "No backtest yet / Start one with Run in the chart's Backtest menu." | list view | Shorten to one line | list header |

## Page: Results (`/results/<run id>`, `pages/results.py`, `prop_firm_card.py`)
| element | today (where) | proposal | new place |
|---|---|---|---|
| Run selector, symbol radio (All symbols / each symbol) | toolbar | Essential | row above strip |
| Title "<Strategy> · <run id>", metas Symbols, Days (UTC), Preset, Run (date), notes | header | Title + Symbols + Days essential; Preset, Run date, notes Details | header, "Details" fold |
| Overview cards: Net R (gross sub), Total trades (wins/losses/BE), Win rate, Avg R:R (planned), Avg realized R, Avg win / avg loss, Profit factor, Expectancy, Max drawdown (gross sub), Longest losing streak | tab Overview, 10 cards with sub texts | Strip (essential): Net R, Trades, Win rate, Profit factor, Max drawdown, Expectancy. Details: Avg R:R (planned), Avg realized R, Avg win/avg loss, Longest losing streak, gross values; sub texts like "if every TP is hit", "by net R" become tooltips | strip + Details |
| Equity curve (R) with Net / Gross / Drawdown (net) legend | Overview | Essential, large | main chart |
| Prop firm card: table of Pass probability (both phases), Failed: daily loss, Failed: max loss, Average days to pass, Median days to pass, Funded account lost within N days; at 0.5/1/1.5 % risk, Fixed vs Adaptive columns | `prop_firm_card.py` | Essential: Pass probability at the middle risk (as strip number "Prop pass %"); full table Details | side panel (collapsed Details inside) |
| HOW_TEXT paragraph ("Estimated by reshuffling...") and "Calculating …" / waiting text | card | Shorten to tooltip "i"; keep progress state as one word | side panel |
| Full Monte Carlo: button, Cancel, Open report, progress bar, status | card | Essential button; progress, status Details | side panel |
| Tab Performance summary: All/Long/Short table (Net R net/gross, Total trades, Wins/losses/BE, Win rate, Avg R:R, Avg realized R net/gross, Avg win, Avg loss, Profit factor, Expectancy, Max drawdown net/gross, streaks, costs: spread, commission, swap, funding) | tab | Details (table kept whole, group rows) | tab below chart |
| Per year, Per quarter (already a fold), R distribution histogram | Performance | Per year essential; quarter and histogram Details | tab below chart |
| Tab List of trades: Entry time (UTC), Symbol, Side, Entry, SL, TP, R gross, R net, Exit, Confluence, Session; hint; row click opens the chart | tab | Essential: time, symbol, side, R net, exit; Entry/SL/TP/R gross/Confluence/Session Details (column toggle) | tab below chart, default tab |
| "No trades." | tabs | Keep as one muted line | n/a |

## Page: Research (`/research`, `pages/research.py`, `research_model.py`)
| element | today (where) | proposal | new place |
|---|---|---|---|
| Title "Research" + HINT sentence | head | Title only; hint to tooltip | header |
| Filters: strategy dropdown, symbol dropdown, flags radio (All / Unflagged only / Flagged only), Min trades input, Reload, "N of M rows" | controls row | Essential: strategy, symbol, flagged toggle, count; Min trades and Reload Details (filter fold) | key strip (strip shows counts: runs, green, flagged) |
| 19-column sortable DataTable, horizontal scroll | table | Replaced by card list (below). Sorting becomes a "Sort by" dropdown (verdict, test net R, net R, R/trade, PF, drawdown) | header right |
| Verdict colours green/yellow/red, flags text with tooltip | table | Essential: verdict as left border colour + chip; flags as amber chips | card |
| Row click opens `/results/...` | table | Kept as a link button "Open results" inside the expanded card | expanded card |

### Research card (one vertical list, no horizontal scroll)
Collapsed card (two lines, wraps at narrow width): `[verdict dot] Strategy · Source(run id + variant)  |  idea one line` then chips: `Period | Trades | Net R | R/trade | Win % | Max DD | PF | OOS (test net R) | MC DD | Prop pass % | Regime | Param. stability | ⚠ flags`. Click anywhere to expand; expanded = tiles with all fields, the sub-table of costs/halves, flags with full labels, link "Open results".

| card field | exists today? | source | note |
|---|---|---|---|
| Strategy + source | yes | `row["strategy"]`, `row["source"]` (`<research id> <variant id>`, or run folder) | keep |
| Variant (name) | yes | `row["variant"]` | expanded |
| Idea in one line | NO | research id/grid file name only; docs in `docs/strategy-*.md`, `knowledge/ideas.md` | new: add `idea` (one line, ideally the strategy spec's first sentence or the grid file's optional `idea = "..."`) to `research.json`; fallback = strategy label |
| Symbols | yes | `row["symbols"]` | expanded |
| Period | yes | `row["period"]` (development period; test period in research.json `periods.test`) | collapsed shows dev; expanded shows both |
| Trades | yes | `scorecard.trades` | |
| Net R | yes | `net_r` | |
| R/trade | yes | `avg_r` ("Avg R" today) | rename |
| Win rate | yes | `win_rate` | |
| Max drawdown | yes | `max_dd_r` (in R) | |
| Profit factor | yes | `profit_factor` | |
| Out-of-sample result | yes, chosen variant only | `test_net_r`, `deflated_sharpe`, `verdict` (test.csv: also `t_stat`, `n_variants`, test `trades`, `win_rate`) | other variants show "not tested" (by rule only one test). Plain runs: none |
| Half 1 / Half 2, costs x1.5, w/o best | yes | `half_first_net_r`, `half_second_net_r`, `net_r_stressed`, `net_r_without_best` | expanded only |
| Warning flags | yes | `flag_keys`, FLAG_LABELS (too few trades, high win rate small edge, one half not profitable, not profitable with higher costs, without best trade, test failed) | chips, labels in expanded |
| Verdict label text (edge / weak / no edge) and reason | partly | test.csv `verdict_label`, `verdict_reason` in `_test_row` (reason not read by `research_model` yet) | expanded; small read change |
| Monte Carlo drawdown | partly | `risk/monte_carlo.py` has `max_dd_pct` median / p95 per run; `tools/monte_carlo --run` writes `results/monte_carlo/<run>/summary.json`; not read per research row | new: compute for the chosen variant, store in `research.json` / test.csv (e.g. `mc_dd_p95_pct`) |
| Prop-firm pass probability | partly | `prop_card_job` / `risk/prop_card.py` computes it for one run folder (Results page); not in research rows | new: per chosen variant, store `prop_pass_pct` (cached) |
| Best market regime | NO | only `ROADMAP V2.6` plans a regime classifier (`analytics/`, spec first, user decides); `orderflow_study.py` mentions regime only internally | new: needs classifier + per-regime net R; card shows regime with best R/trade and the worst below it in Details |
| Parameter stability | NO | variants.csv has the whole grid (net R per variant, `set.<setting>` columns) so it is computable | new: e.g. share of grid variants (neighbours of the chosen one) with net R > 0, or net R spread; define in spec |
| Plain runs (no research) | yes for scorecard, none for MC/regime/stability/idea | `_plain_row` | show "-" for new fields; they sort after research rows |

Sort default stays: verdict, test net R, net R. List is virtualised/paged (hundreds of runs): render first 50 cards, "Show more".

## Page: Live (`/live`, `pages/live.py`, `live_model.py`, `trading_panel.py`)
| element | today (where) | proposal | new place |
|---|---|---|---|
| State badge, strategy name, metas (symbols, session window + countdown, running since) | header | Essential (one line) | top strip left |
| Buttons Start, Pause/Resume, Stop, Close all & stop (+ confirm "Close ALL positions opened by the bot and stop it. Continue?") | header | Essential; Close all & stop in red, confirm kept | strip right |
| Notes "Bot not started yet (no status file).", "No heartbeat for N min: the bot is not running.", "Last error: ..." | header | Shorten (state chip text; last error stays in red) | strip |
| Cards: Balance (start), Equity (floating), Today (% bar, money, R, daily stop), FTMO limits (bars), Heartbeat + MT5 connected | cards | Essential | strip |
| Recent trades bar chart + range picker + "Click a bar to open the trade on the chart." | `lv-two` right | Essential chart; hint to tooltip | main chart |
| Setup in progress (per symbol funnel with step dots) | fold | Essential, compact | side panel |
| Open positions | fold (open) | Essential | tab below chart (default) |
| Closed trades: Entry (CH), Symbol, Side, R, Chart link; range picker | fold | Essential table | tab below chart |
| Today's signals and skips | fold | Details | tab below chart |
| Event log ("last N, times in Swiss time") | fold | Details | tab below chart |
| Settings: Risk per trade (%), Daily stop (%), Symbols; note "Editable only while the bot is not running..." | fold | Fields essential in a tab; note to tooltip | tab below chart |
| Connection: Account (Platform, Login, Password, Server, Terminal path), Symbols on the server, Telegram (Bot token, Chat id, Save Telegram, Send test message), Demo test orders (+ Run), Test connection, Save; ~12 helper notes ("The account number.", "Never shown again after saving.", ...) | fold "Connection · MT5 account and Telegram" | Details/Settings; all helper notes become tooltips; Telegram and Demo test orders each a sub-fold | Settings tab (top right gear) |

## Page: Risk (`/risk`, stub)
| element | today | proposal | new place |
|---|---|---|---|
| Greyed "Risk" tab, tooltip "Not built yet" | `nav.py` | Keep as disabled tab or hide until built; planned content per `docs/risk-management.md` (preset, RiskConfig, pass rate vs risk, equity fan, failure breakdown, sweep heatmap) fits the standard skeleton: strip = pass %, fail daily, fail max; chart = equity fan; side = RiskConfig; tabs = sweep heatmap / failure breakdown | later |

## Text cuts (the "too much text" list)
- Monte Carlo `HOW_TEXT` (5 lines) to one tooltip.
- Settings notes and Live Connection notes (about 15) to tooltips.
- Hints: Research `HINT`, Results "Click a trade...", Live "Click a bar...", Chart "Used by the Trades overlay and the backtest.", Backtest list sub-texts: remove or one muted line.
- Card sub-texts in Results overview ("if every TP is hit", "by net R", "net R won / net R lost", "net R per trade") to tooltips.
- Module docstring-like texts are not UI; no change.

## Open questions for the user
1. Light or dark only? The proposal makes everything dark (also the Results trade table, today light). OK, or keep a light switch?
2. "Idea in one line" for each research card: write it in the grid file (`idea = "..."`, you or Gemini write it) or derive it from the strategy spec automatically?
3. "Best market regime" and "parameter stability" need new analytics (regime classifier is a ROADMAP V2.6 item, "spec first, user decides"). Show "-" now and fill later, or should I include them in this redesign task? Parameter stability definition: share of neighbouring grid variants with net R > 0?
4. Monte Carlo drawdown and prop-firm pass % per card cost compute time (full MC ~35 min; the prop card is faster). Compute only for the chosen variant per research (my proposal), or for every variant?
5. Keep the grey "Risk" tab, hide it, or merge it into Backtest results and later Portfolio?
6. Chart page: move Backtest run form and Strategy dropdown from toolbar popovers to tabs below the chart (proposal), or keep them as popovers to stay close to today's workflow?
