# Brief: V2.5b — Research page as one vertical list of cards

Context: ROADMAP › V2.5 (decisions of the user 2026-10-23 in `docs/design/ui-proposal.md` ›
Page: Research and › Research card; read both fully). V2.5a (commit ba05aab) added the dark
tokens (`ui/assets/theme.css`) and helpers (`ui/layout.py`: `page`, `key_strip`, `details`,
`info`, `tabs_below`). Since the proposal was written, every research run also writes these
files in `results/research/<id>/` (all optional; old runs lack them): `significance.json`
(Reality Check p, PBO, N / N_eff), `bayes.json` (P(mean R > 0), posterior odds),
`skill_bounds.json` (detrended net R, BCa lower bound, log PF), `sensitivity.csv` + the
report's gentle / sharp verdict, `walk_forward.csv`, `drawdown_bounds.json` (per run folder),
`monkeys.json`, `profile.json` (best condition per dimension, strongest skill cells),
`grid.csv`, flags in `variants.csv` / `test.csv`. The data layer is `ui/research_model.py`.

## What to build

1. **Data** (`ui/research_model.py`): each research row reads the files above for its
   **chosen** variant (other variants: "–"), robustly (missing / broken file -> "–", never an
   error). New row fields: `idea` (grid file `idea = "..."` in `research.json`; fallback the
   strategy label; add the optional `idea` key to the grid loader and `research.json` if
   missing), `rc_p`, `pbo`, `n_eff`, `p_mean_pos`, `detrended_net_r`, `lower95`,
   `sensitivity` (gentle / sharp), `wfe`, `mc_dd_p95_pct` and `prop_pass_pct` (from the chosen
   variant's Monte Carlo summary when present; else "–"), `monkey` (pass / fail of kind 1),
   `best_regime` and `best_condition` (from `profile.json`: the strongest skill cell, or
   "none").
2. **Card list** (`ui/pages/research.py`): replaces the DataTable. Collapsed card: verdict
   colour as the left border + a dot, `Strategy · source`, the idea line, then chips
   `Period | Trades | Net R | R/trade | Win % | Max DD | PF | OOS net R | Detrended | MC DD p95 |
   Prop pass % | Best condition | Sensitivity | ⚠ flags`. Click expands: tiles with every field
   (incl. halves, costs x1.5, without best, RC p, PBO, N / N_eff, P(mean > 0), lower bound,
   WFE, monkey percentiles), full flag labels, a link "Open results" (today's row click target).
   No horizontal scroll at 1280 px and at 800 px (chips wrap). First 50 cards, then "Show more".
3. **Controls**: key strip with counts (runs, green verdicts, flagged); filters strategy,
   symbol, flagged toggle; "Sort by" dropdown (verdict, test net R, net R, R/trade, PF,
   drawdown, detrended, RC p); Min trades and Reload inside a `details()` fold. Hint text ->
   `info()` tooltip.
4. Plain runs (no research) keep their card with "–" for research-only fields, sorted after
   research rows (as today).

## Answers given up front (Opus, 2026-10-24)

- Keep the existing filter / sort logic and its tests; only the rendering changes. Ids used by
  callbacks stay or are updated together with their callback and test.
- Verdict colours: green = edge, amber = weak, red = no edge, grey = not tested.
- Numbers: R with 1 decimal for totals, 2 for per-trade; percentages without decimals; p-values
  2 decimals; "–" for missing.
- No new dependencies. Never start a server and leave it running (AGENTS.md); Opus does the
  browser check.

## Rules

Test-case list first: a research folder with all files -> every chip filled; with none of the new
files -> "–" and no error; a broken JSON -> "–"; sort by each option; filters; "Show more"
paging; the card renders without a horizontal-scroll element (no fixed widths > the container);
plain runs after research runs. Run only the UI tests (`pytest -q tests/ui >
results\pytest_v25b.log 2>&1`); Opus runs the full suite. Never edit `src/backtester/live/`.

Done = UI tests green, `ruff check .` clean. Report: files changed, ids changed, decisions the
proposal did not settle, open questions.
