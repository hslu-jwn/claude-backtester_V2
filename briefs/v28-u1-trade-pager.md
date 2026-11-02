# V2.8 U1: chart Trades tab in pages of 100 (Codex gpt-6.1-terra, medium)

Read `AGENTS.md` first. Rule: ROADMAP V2.8 (2) U1, picked by the user 2026-11-02. Audit:
`docs/review/finalization-audit-2026-11-02.md`.

## Problem

`src/backtester/ui/pages/chart.py` `newest_trade_rows` puts every trade of the newest saved run
into the chart page layout (`run-trades-list`). The newest run now has 10,397 trades: the chart
page response is 6.4 MB with 10,671 pattern-matching buttons (`{"type": "run-trade", ...}`,
watched by the `ALL` input of `_focus_trade`), and the browser needs ~30 s or more before the
chart is usable. With the list removed the page is usable in 2.5 s.

## What to build (test-first: write the tests below first, see them fail, then the code)

1. `chart_side.py`: `RUN_TRADES_PAGE = 100` and
   `trade_page(trades, sort, page, size=RUN_TRADES_PAGE) -> (rows, page, pages)`:
   sort with the existing `sort_run_trades(trades, sort)`, `pages = max(1, ceil(n / size))`,
   `page` clamped to `1..pages` (also for 0, negative, None, too large), `rows` = that slice.
2. `chart.py` `newest_trade_rows(results_dir, sort="time", page=1)` returns
   `(list_div, label, page, pages)`: one page of `chart_side.trade_item(t, "run-trade")` rows
   (no `--pair-rank` style any more), label `"1-100 of 10,397"` (thousands separator;
   `"No trades."` and an empty list without a run or trades).
3. Layout of the Trades tab: `run-trades-list` starts **empty** (filled by a callback), the
   existing Time / Pair radio and Minimize button stay; add a pager in `ch-run-trades-head`:
   `html.Button("‹", id="run-trades-prev")`, `html.Span(id="run-trades-label")`,
   `html.Button("›", id="run-trades-next")` (class `tb-btn`, `n_clicks=0`) and
   `dcc.Store(id="run-trades-page", data=1)`.
4. Callbacks in `register_callbacks` (keep `results_dir` handling as the other callbacks do):
   - page: Inputs `run-trades-prev.n_clicks`, `run-trades-next.n_clicks`,
     `run-trades-sort.value`, State `run-trades-page.data` -> `run-trades-page.data`;
     sort change -> 1, prev -> page - 1, next -> page + 1, clamped with the newest run's
     trade count (`chart_side.run_trades`, already cached by mtime); `prevent_initial_call=True`.
   - render: Inputs `run-trades-sort.value`, `run-trades-page.data` ->
     `run-trades-list.children`, `run-trades-label.children`, `run-trades-prev.disabled`,
     `run-trades-next.disabled` (runs on the initial load).
   - Delete the `run-trades-list.className` callback, `chart_side.run_trades_class` and the
     two `.ch-by-pair` rules in `assets/chart-page.css` (the CSS `order` trick is replaced by
     the server-side sort). Keep Minimize (`run-trades-collapsed`, `_run_trades_apply`) and
     `_focus_trade` (its `ALL` input now sees at most one page) unchanged.

## Tests (new file `tests/ui/test_run_trades_pager.py`; reuse the helpers in `tests/ui/test_chart_side.py`)

- `trade_page` with 250 trades by time: page 1 = the 100 earliest in time order, page 3 = the
  last 50, page 4 -> page 3, page 0 / None / -2 -> page 1, `pages == 3`; empty -> `((), 1, 1)`.
- Pair sort across a page boundary: page 2 continues the pair order (symbol A..Z, each pair by
  time) exactly where page 1 stopped.
- `newest_trade_rows` with 3 trades: ids `[3, 2, 1]` by time, label `"1-3 of 3"`, no `style`
  with `--pair-rank`; "pair" gives NAS100 first; no run -> `"No trades."`.
- Layout with a run of 1,000 trades in `tmp_path`: no `"run-trade"` id in `str(layout)`, the
  pager ids are there, and `len(json.dumps(layout, cls=plotly.utils.PlotlyJSONEncoder))` stays
  far below the trades' size (assert < 400,000 bytes).
- Page callback: next 1 -> 2, next on the last page stays, prev on 1 stays 1, sort change -> 1.
- Render callback: 250 trades, page 3 -> 50 rows, label `"201-250 of 250"`, prev enabled,
  next disabled; page 1 -> prev disabled.
- Replace the two old tests in `tests/ui/test_chart_side.py` that pin the CSS-order design
  (`test_newest_trade_rows_are_in_time_order_and_carry_their_pair_rank`,
  `test_sort_switch_only_changes_the_list_class`) by the new ones above (the user changed the
  design 2026-11-02); keep `test_layout_has_the_run_trades_controls` and add the pager ids.
- `tests/ui/test_v25c_pages.py::test_moved_backtest_callback_and_newest_trade_focus` must pass
  unchanged.

## Limits

Touch only `src/backtester/ui/pages/chart.py`, `src/backtester/ui/chart_side.py`,
`src/backtester/ui/assets/chart-page.css`, `tests/ui/test_run_trades_pager.py`,
`tests/ui/test_chart_side.py`. No new dependency, no other behaviour change. Never start the
app or any server; never commit, push or branch.

**Done =** `python -m pytest tests/ui -q` green, `ruff check .` and `ruff format --check` on the
touched files clean. Report: files changed, test results, open questions.
