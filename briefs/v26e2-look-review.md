# Brief: V2.6 step 5 — 4.3 look and layout items chosen by the user (2026-10-26)

Opus walked every page in the browser; the user picked these three. V2.5 look rules
(`ui/layout.py`, tokens, `info()`, `details()`, essentials visible, the rest behind Details).
No trading rule or default changes. Same rules as `briefs/v26e-ui-items.md` (test-first, never
start the app, keep existing ids, no new dependencies, never edit `src/backtester/live/`).
Run only your tests (`pytest -q tests/ui > results\pytest_v26e2.log 2>&1`) + ruff.

1. **Live page: mark stale status.** When the bot's heartbeat is older than a threshold
   (setting, default 5 minutes; the bot is "not running"), the key strip and panels must not
   look current: show "Not running · last seen <local time> (<age>)" instead of "MT5 connected";
   grey out Today / FTMO limits / Setup in progress with a "last session <date>" label; keep the
   numbers (they are the last known state). Read-only change in `ui/` (`live_model.py`,
   `pages/live.py`, css); never `src/backtester/live/`. Tests: fresh heartbeat -> unchanged;
   old heartbeat -> stale labels, "connected" never shown; no status file -> as today.
2. **Research card: hide empty tiles.** In a card's details, tiles whose value is missing
   ("-", not computed yet) move into a closed `details("Not computed yet (N)")` at the end;
   filled tiles keep their order. Card header metrics unchanged. Tests: N counts, order kept,
   no tile lost.
3. **Chart: candles before trades.** On load / symbol / timeframe change, draw the candles as
   soon as they are read; the strategy's trades (trades overlay, `registered_run`) and the stats
   strip fill in when their run finishes (with the existing progress indicator), so the chart
   is never empty while trades compute. Keep the review-mode no-peek clipping exactly as it is
   (its tests must stay green). Tests: the candle callback does not wait for / depend on the trade
   run; trades arrive in a separate output.

Report: files changed, test results, ids added / changed.

## Fix after Opus's browser check (2026-10-26)

Item 3 regression: on the Chart page (AUDUSD, M5, strategy 3, default range) the candles appear
first and the trades arrive and are drawn (also in "Trades in view"), but the stats strip above
the chart (Net R, Win rate, Trades, Max drawdown) stays "—" forever (checked for 73 s; before the
change it showed -85.38 R, 48.9 %, 274, 88.11 R). No server error is logged. Make the stats
strip fill when the trade run finishes (same values as before), and add a test that drives the
real callback chain: candles -> trade run result -> stats outputs filled (the current tests
evidently miss the wiring, e.g. a missing Input / wrong trigger / `no_update`). Run
`pytest -q tests/ui > results\pytest_v26e2_fix.log 2>&1` + ruff.
