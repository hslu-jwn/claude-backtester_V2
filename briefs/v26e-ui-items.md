# Brief: V2.6 build step 5 — review mode, trade inspection, parameter heat map, dropdown

Context: ROADMAP › V2.6 build order step 5; V1 items 3.3d, 3.5, 12.4, 4.3 in
`docs/archive/ROADMAP-v1.md`; decisions of the user 2026-10-26 below. The chart shows any
strategy's trades since V2.4a (`ui/trades_overlay.py` `registered_run`); replay exists on the
chart; `ui/trade_focus.py` exists. Look: V2.5 (`ui/layout.py`, tokens, `info()`, `details()`).
No trading rule or default changes.

## 1. Review mode (3.3d; decision: every strategy)

On the Chart page a "Review" mode: pick strategy + symbol + period (development period by
default); the app runs the strategy (reuse `registered_run`) and steps through its trades one by
one (Next / Previous / jump to first unlabelled). For each the user marks **take** or **skip**,
an optional short reason (<= 200 chars) and an optional own TP price; saved to
`results/review/<strategy>.jsonl` (one line per label, last label per key wins; key = strategy,
symbol, entry time UTC, direction; plus the settings hash of the run, label time).
- **No peeking (Opus answer):** while judging, the chart shows candles only up to the entry
  candle's close (the decision time); a "Reveal outcome" button then shows the rest and the
  trade's result. Use the existing replay / view-limit mechanism; never send future candles to
  the browser before reveal.
- **Agreement %:** for the current settings, of the user's labelled setups: "take" labels whose
  trade still exists + "skip" labels whose trade no longer exists, divided by all labels;
  shown in the review panel with counts, and per settings hash in a small history table, so the
  user sees how a rule change moved agreement.

## 2. Trade inspection (3.5, generalised; decision: every strategy)

Click a trade (position box / marker) on the chart -> focus: draw that trade's setup: entry,
SL, TP(s), exit, and for strategy 1 its zones / confluences (existing overlays); for others
whatever the strategy records about the decision (order note / reason fields if present; do not
invent detector output). A "Replay this trade" button starts the existing replay a configurable
number of candles (default 50) before entry. Click outside the chart or press Escape -> off.
Strategy 1 keeps `strategy-session-zones.md › Session inspection view` behaviour (click a
session line -> that session); update that spec section to say the generic trade inspection now
covers the other strategies.

## 3. Parameter heat map (12.4; decision: on the research card)

In a research card's details: two dropdowns with the grid's varied parameters (axes) and a
metric (net R, R per trade, win rate, trades; **development period only**, from the grid's
variant table). Parameters beyond the two axes are fixed at the chosen variant's values; cells
without a variant stay empty (not zero). The chosen variant is marked. Plotly heatmap with
the V2.5 colours (diverging around 0 for R metrics), hover shows the variant id and all its
values. A grid with fewer than two varied parameters shows a one-line note instead.

## 4. Strong-move filter switches -> dropdown (4.3 known wish)

The strong-move filter switches (FVG, OB) in the settings panel become one dropdown (off / FVG
/ OB / both, mapping to exactly the same settings as the switches today). Settings JSON,
presets and grids keep the same keys and values (no migration); only the control changes.

## Answers given up front (Opus, 2026-10-26)

- Review labels never change a rule or a setting; they are data for the user.
- Keep all existing ids used by callbacks and tests; list any change.
- Tests never start the app; callbacks tested as functions (as the existing UI tests do).
- No new dependencies.

## Rules

AGENTS.md (no commit / push / branch; no lingering processes; never `src/backtester/live/`; no
credentials). Test-case list first (`briefs/v26e-test-cases.md`), then tests (`tests/ui/...`),
then code. Must-have tests: review mode never serialises a candle after the entry candle's close
before reveal (no-peek); label round trip and "last label wins"; agreement % on a hand-built
case (rule change removes one take and one skip trade); inspection draws exactly the clicked
trade; heat map grid with 3 varied params fixes the third at the chosen variant and leaves empty
cells empty; dropdown maps 1:1 to the old switch values (all four combinations). Run only your
tests (`pytest -q tests/ui > results\pytest_v26e.log 2>&1`) + ruff on touched files. Report: files
changed, test results, ids added / changed, open questions.
