# Project review, 2026-11-11 (Claude Fable 5.2, read-only)

Scope: umbrella `AGENTS.md`, V2 `AGENTS.md`, `CLAUDE.md`, `docs/`, the three skills, then `src/`,
`tests/`, `knowledge/`, `research/`. Paths are relative to `backtester-claude_V2/`. No project file
was changed; this report is the only file written.

**How far the review went.** Read in full: `core/series.py`, `core/mtf.py`, `engine/trade.py`,
`engine/backtest.py`, `engine/costs.py`, `engine/spread_table.py`, `engine/replay.py`,
`data/resample.py`, `data/adapters/cache_adapter.py`, `strategy/base.py`, `strategy/timed_hold/`,
the split logic in `tools/research.py`, HANDOFF, agent-routing, the skills, `cost-wall.md`,
`research/candidates/README.md`, the last two research-log entries. Skimmed by grep only: the other
13 strategies, detectors, risk, analytics, UI, most tools. Not opened: `.env`, `src/backtester/live/`.
Anything marked **UNVERIFIED** was not checked against code or a source.

**Test run (HEAD `b6c410a`, 2026-11-11):** 5,710 passed, **2 failed**, 14 skipped, 4 xfailed in
9 min 41 s. Both failures are `tests/test_layers.py::test_imports_follow_the_layers` (see B6).

**What looked sound.** The no-lookahead core holds up: `SeriesView` cannot return a candle past
its cursor, higher timeframes are visible only after their close, daily candles close at 17:00 New
York, limit orders must have been placed one step earlier, M1 replay falls back to SL-first when
minutes are missing, and `tests/strategy/test_contract.py` runs a future-candles test for every
registered strategy. I found no lookahead leak in the files I read.

---

## A) Workflow improvements

| # | Problem | Fix | Effort | Gain |
|---|---|---|---|---|
| 1 | **One result is recorded in five places:** spec › Results, `docs/research-log.md`, HANDOFF, the candidate row / idea card, `knowledge/topics/cost-wall.md`. "Was X tested?" needs a grep over about 250 KB, and copies drift (cost-wall §5 still says the spread proposal is "not wired in"). | One committed `research/ledger.csv`: id, family, mechanism label, cells, dev period, trades, gross / cost / net R per trade, gates, test spent (date), verdict, spec path. The cost-wall table and the HANDOFF research part link to it. | M | One lookup instead of five; the honest trial count comes for free; fixes B2 and B7. |
| 2 | **Screen after build, not before.** Most of the ~25 falsified hypotheses went spec → Codex build → sol review → gates tool, then died on "gross edge below cost". `time_of_day_profile` showed a 100-line screen answers that in minutes. | Make "screen first" a hard step in the skill for any idea that is a fixed clock window or a daily-bar rule: gross bp per trade vs cost from the cost table; only survivors get a spec. Screens are logged in the ledger. | S | Most ideas end in minutes instead of one Codex window. |
| 3 | **A gates tool is written per strategy:** `alternating_path_gates.py` (252 lines), `h1_shock_gates.py` (317), `timed_hold_gates.py` (528, also holds the energy and daily-reversal gates), each with its own bootstrap / halves / integrity code. | One `tools/gates.py` reading a `[gates]` table from the grid TOML (min trades, costs x2, halves, breadth, best-date removal, bootstrap bound, integrity); strategy extras as small functions. | M | One dispatch and one review less per hypothesis; gates are fixed in the committed grid, not in code written near the run. |
| 4 | **Contradicting instructions.** `AGENTS.md:78-80` (Opus decides unclear points) vs `:82-83` (stop and ask, never guess). `AGENTS.md:166-167` (do one step, then stop) vs CLAUDE.md never-idle. Skill `:68-69` (do not judge pass / fail, the user decides) vs `:70-78` (`Test=auto` runs the test after a pass). Skill `:18-19` (ask and wait) vs never-idle. Skill `:8` lacks `Test=`. Two Telegram rules in CLAUDE.md (`:73-75`, `:76-83`) plus a third in the skill (`:19`). Routing table "Codex failed twice → Sonnet" vs "Sonnet never for heavy builds". | One pass: rules per mode (`Continue.Code`: stop and ask; `Continue.Research`: decide, record the assumption). One Telegram rule. | S | Fewer wrong stops and repeated questions. |
| 5 | **HANDOFF is 227 lines / 18 KB** and read first in every session. It says "current state only" but keeps the 2026-11-03 state and 13 closed ☑ items, and contradicts itself (see B10). | Cap at about 60 lines: state, open decisions, next step. Closed items live in git. | S | Fewer tokens per session, one state. |
| 6 | **Nine-minute suite before every commit** (rule "full suite once before a commit" plus "commit after every step"). The 30 slowest tests take 182 s of 582 s; the top three alone 56 s (`test_monkeys` 29.5 s, `test_filelock` 15.2 s, `test_ts_gates` 11.7 s). The red suite (B6) shows the rule is not followed anyway. | Per commit: tests of the touched package + `tests/strategy/test_contract.py` + `tests/engine` + `tests/test_layers.py`. Full suite at `End.` and before a push. Shrink the three slowest (fewer runs, same assertion). | S | About 7 minutes per step; a rule that is actually kept. |
| 7 | **Routing overhead.** `agent-routing.md` has 12 worker rows over 7 providers, four dated rule blocks on top, two rows "not enabled", and model IDs repeated in the `ai-dispatch` skill and CLAUDE.md. In practice heavy work waits when Codex is out (HANDOFF Open 14). | Three routes: local tools, coordinator, Codex; one free model for literature. Drop unused rows (deepseek, GitHub Models, claude46). IDs only in the routing doc. | S | Less deliberation per task, no stale IDs. |
| 8 | **Stale facts in the entry docs:** AGENTS.md says 9 strategies and 26 symbols (14 strategy folders, HANDOFF says 34 symbols); its spec table lacks strategies 8 and 10-13, `news.md`, `portfolio.md`; README says 7 strategies. | Remove counts; replace the table by "every `docs/strategy-*.md`, list in `strategy/registry.py`". | S | Nothing to keep in sync. |
| 9 | **Specs carry results.** `strategy-timed-hold.md` is 46 KB with 12 hypotheses and their results; `research-runner.md` 54 KB, `risk-management.md` 64 KB. Every worker brief says "read the spec section". | Results move to the ledger (A1); one hypothesis per short section; dated history out of the rule text. | M | Smaller briefs and worker context. |
| 10 | **Lane and brief leftovers:** both lane worktrees (`bt-lane-energy_report`, `bt-lane-daily_reversal`) and `lanes.json` entries still exist after the merge `47f5aff`; 111 files in `briefs/`, only a few still open. | `lanes remove` becomes the last step of a lane merge; done briefs move to `docs/archive/briefs/` at `End.`. | S | A clean list of what is really open. |

---

## B) Potential problems, by severity

**B1. High. The live-fill spread raises do not reach the five most-traded symbols.**
`src/backtester/engine/costs.py:418-421`: when the spread table has a value it wins, and the fixed
spread is never read. The default table (`engine/ftmo_spread_median.json`) covers exactly XAUUSD,
GBPUSD, GBPJPY, NAS100, US500. Checked with the default `CostConfig()` at 2026-10-06 14:00 UTC:
GBPUSD uses 0.00002 (fixed 0.000059), GBPJPY 0.014 (0.023), NAS100 1.45 (1.9), US500 0.56 (0.61).
`tests/engine/test_live_fill_defaults.py:57` passes because it sets `spread_table=None`.
*Scenario:* the fill report found GBPJPY 2.25x, GBPUSD 1.97x, NAS100 1.95x under-charged; commit
`d0bbcd8` raised their fixed spreads, yet every default run on these symbols, including one-time
tests on 2021+, still charges the old median. *Fix:* use `max(table value, price-scaled fixed
spread)`, or rescale the table by the live ratio; add a test with the default config.

**B2. High. One forgotten flag spends the test period.** `src/backtester/tools/research.py:337-338`
returns "authorized" for every grid without a `[submission]` table (46 of 48 grids), and the CLI
default (`:1417`, `:1130-1173`) is development plus test. "Once" is enforced only by
`results/research/<id>/research.json`, which is git-ignored and keyed by a hash of the grid.
*Scenario:* `python -m backtester.tools.research research/grids/us_close_de_open.toml` without
`--dev-only` picks the best development cell and runs it on 2021-09-14 onward; editing one cell or
the grid name allows a second "first" test. *Fix:* make the test opt-in (`--test`), and let it
check a committed ledger row per strategy and symbol set (A1).

**B3. High. The test period was already used for one of the pending "one-time" tests.**
`src/backtester/tools/open_gap_study.py:144-145` and `noise_study.py:179-180` default to
2020-01-01..2026-09-30; `strategy2_explore.py:301-302` to 2023..2026. `docs/strategy-gap-fade.md:47`
names halves "2020-22 / 2023-26", and `docs/archive/ROADMAP-v1.md` 11.4 / 11.6 / 11.7 ran the 36
gap-fade variants on 2020-2026 and on FTMO data from 2021-09. HANDOFF Open 1 still lists gap fade
as a pre-registered one-time MT5 test. *Scenario:* gap fade "passes" on a period its rule was
shaped on and is reported as confirmed. *Fix:* record gap fade's test as not clean (forward demo
data only); give the three tools a default end of 2021-09-13 and `--allow-test-period`, as
`gap_bucket_study.py:92` has. Whether the "quiet sideways" regime definition for gap momentum also
saw test data is **UNVERIFIED**.

**B4. High for multi-day index holds. No dividend adjustment.** The word "dividend" appears nowhere
in `src/backtester/`. Cash-index CFDs drop by the dividend points on ex-dividend days. *Scenario:*
a multi-day short on UK100, AUS200 or EU50 collects those drops (about 3-4 % per year, my estimate)
for free and a long loses them, so F4M, RSI(2), `daily_reversal` and index trend results are biased
(shorts flattered). GER40 tracks a performance index and is not affected. How FTMO books dividends
is **UNVERIFIED**: check the demo deal history for an index position held over an ex-date. *Fix:* a
dividend-points table charged on holds across ex-dates, or treat multi-day index shorts as gross
only until measured.

**B5. Medium-high for multi-day holds. Today's swap sign is applied to every year.**
`src/backtester/engine/costs.py:175-176`, `:248-249` (USOIL long +4.966, UKOIL long +6.097 USD per
lot per night, about +19 % per year on the notional by my arithmetic), `:205`, `:239-242` (long JPY
pairs credited). Price scaling (2026-11-09) keeps the sign. *Scenario:* a multi-day long in oil in
2015-16 or 2020, when the curve was in deep contango and real long financing was a cost, is credited
instead; the same for long USDJPY in zero-rate years. *Fix:* clamp positive swap to zero in research
runs (one line in `swap_r_nights`) until a rate history exists; report swap as its own gate line.

**B6. Medium. The suite is red at HEAD.** `tests/test_layers.py:66` fails for
`src/backtester/strategy/daily_reversal/strategy.py:20` (`from backtester.engine.costs import
TICK_SIZES` at runtime) and `src/backtester/strategy/energy_report/strategy.py:15`
(`from backtester.engine.trade import TradeResult` outside `TYPE_CHECKING`). Both files came in with
the lane merge `47f5aff` (2026-11-10); 28 commits were pushed on top. Which commit first failed is
**UNVERIFIED**. *Scenario:* a strategy that reads engine tables can drift from what the engine
applies, and "tests green" in the log is not true. *Fix:* move the `TradeResult` import under
`TYPE_CHECKING`; pass the tick size in through the existing `configure_costs` hook.

**B7. Medium. The multiple-testing record is not versioned.** `.gitignore` excludes `results/`;
`src/backtester/analytics/trial_log.py:28,44` writes `results/trials.jsonl`; the test-spent state is
in `results/research/`. *Scenario:* a disk failure, `git clean -fdx` or a second PC resets the trial
count behind the deflated Sharpe to zero and re-opens every one-time test. *Fix:* the committed
ledger (A1), or copy `trials.jsonl` into the repo at `End.`.

**B8. Medium. Shorts pay the entry-time spread at the exit and at the stop.**
`src/backtester/engine/backtest.py:453,502` stores the spread once at entry;
`src/backtester/engine/trade.py:225-230,345` uses it for the short's stop trigger and exit fill.
Longs are right (they pay at entry). *Scenario:* a short opened at 14:00 New York and held through
the 17:00 rollover, where live spreads were about 5x (fill report), is never stopped by the wider
ask and exits cheaply. *Fix:* look up the spread at the managing candle's time for shorts, with a
test on a rollover-hour candle.

**B9. Low-medium. Fixed quote-to-USD rate for commission and per-lot swap.**
`src/backtester/engine/costs.py:131,238-242,258-265`. USDCHF uses 1.2088 (2026); at 2015-21 prices
its commission in price units is about 17-20 % under-charged (my arithmetic). USDJPY and USDCAD err
the conservative way. *Fix:* for USD-base pairs use `1 / entry price`.

**B10. Low. Stale state that can misdirect an agent.** `docs/HANDOFF.md:71` (branch not merged) vs
`:166` (merged 2026-11-03); `:59-61` and `:219` (spread proposal not applied, waiting on the user) vs
`:174` (done `d0bbcd8`); `knowledge/topics/cost-wall.md` §5 the same. *Scenario:* an agent applies
the proposal a second time or asks the user again. *Fix:* A5.

Also seen, not ranked: `src/backtester/risk/account_sim.py`, `risk/config.py`, `risk/sweep.py` are
docstring-only "TODO: implement" files while the docs call these parts built (see C).

---

## C) Delete or merge

**Delete**
- `src/backtester/risk/account_sim.py`, `risk/config.py`, `risk/sweep.py`: 4-5 lines each, docstring
  plus "TODO: implement"; nothing imports them (only the `risk/__init__.py` docstring names them).
- Intake remnants: `_test_authorized` and the `results/intake/` path in `tools/research.py`, the
  `[submission]` handling, the `intake` extra in `pyproject.toml`. The ledger check (B2) replaces them.
- Lane worktrees `../bt-lane-energy_report`, `../bt-lane-daily_reversal`, their `lanes.json` entries
  and branches. Other old local branches (`lane/review_h1`, `v2-setup`, `v2-review`, `v2-grid-merge`,
  `v2-chart-trades`, `docs/v2.4e-economic-calendar`) show as merged into `v2-6-research`;
  `wip-a2a3-gemini` does not, look before deleting.
- `research/grids/orb_example.toml`, `check_gap_fade.toml`, `check_orb.toml` if no test reads them
  (**UNVERIFIED**).

**Merge**
- The three gates tools into one (A3); the four bootstrap spots (`analytics/bootstrap.py`,
  `risk/bootstrap.py` shim, `alternating_path_gates.block_bootstrap`, the two in
  `timed_hold_gates.py`) into `analytics/bootstrap.py`.
- `docs/research-log.md`, `knowledge/topics/cost-wall.md` §1, candidate statuses and HANDOFF research
  notes into the ledger plus one short log (A1).
- Model lists in the `ai-dispatch` skill and CLAUDE.md into `docs/agent-routing.md` (the umbrella
  AGENTS.md already says IDs live only there).
- Spec file names: `strategy-daily_reversal.md` (underscore) vs `strategy-gap-fade.md` (hyphen); pick one.

**Move to archive**
- `briefs/`: 111 files, keep the open ones (`multi-symbol-1a.md` and the lead-lag briefs).
- `docs/review/` (27 one-off reports), the "Earlier state" half of HANDOFF, the 38 finished ☑ steps
  in `docs/ROADMAP.md` (442 lines), as was done for V1.
- `knowledge/research/reports/R007..R024_INDEPENDENT_REVIEW_PACKET.md` and the 18 M15 JSON drafts in
  `research/candidates/`: all triaged out on 2026-11-09; the triage report is enough.
  `knowledge/research/research_log.md` (84 KB, the department's log) is already in `../archive/`.
- One-off study tools for parked strategies (`strategy2_explore.py`, `no_wick_retest_study.py`,
  `noise_study.py`, `open_gap_study.py`): results are recorded, two default to the test period (B3),
  and their tests cost runtime.
- The 20 `research/grids/timed_hold_*.toml` of falsified hypotheses into `research/grids/done/`.

---

## D) Research and strategy ideas: UNTESTED, not recommendations to trade

Read first: `cost-wall.md`, `research/candidates/README.md`, `knowledge/ideas.md` (overview), the four
idea harvests, the research log of 2026-11-09 / 10. Not repeated here because already tested,
screened out or drafted: clock-window FX and index effects, fix effects, Gotobi, turn of month
(unconditional), FOMC morning and FOMC cycle, RSI(2), Connors, Turtle Soup, EIA oil, ORB, gap fade /
momentum, H1 shock, M15 bar patterns, crypto trend / intraday, FX carry, overnight drift, the five
lead-lag specs, pair drafts, Melvin-Prins (marked dead), the Zarattini noise-area rule (reviewed;
my reading: about 3.8 bp per day after ETF costs does not survive CFD costs).

The cost wall leaves little room, so this list is short on purpose. Citations are from memory and
**UNVERIFIED** unless the project already opened them.

**1. Capitulation recovery, the frozen CAP rule on more data.**
*Mechanism:* after forced selling, whoever provides liquidity is paid; reversal returns rise with
volatility. CAP was not falsified, it was inconclusive (+5 to +7 R on 32 trades, minimum 80).
*Reuse:* `strategy/daily_reversal` (`setup=CAP`), the daily gates in `timed_hold_gates.py`,
`--cache-dir data/cache/histdata_presample` (indices 2010-11..2014).
*Cheap test:* the unchanged rule on pre-sample plus development data, pooled. *Kills it:* still under
80 trades; doubled-cost net ≤ 0; bootstrap lower bound ≤ 0; more than half the profit from March 2020.
Longs are hurt by B4, so the bias is conservative. *Prior art:* Nagel 2012 "Evaporating Liquidity";
keywords "short-term reversal VIX", "liquidity provision returns".

**2. Month-end rebalancing pressure with a conditional sign.**
*Mechanism:* funds with fixed weights and month-end cash needs sell equities after a strong month and
buy after a weak one; the direction is known before the trade. The unconditional turn of month (F4,
F4M) was falsified; the conditional sign was, as far as I can see in the spec, not tested
(**UNVERIFIED**). `2026-11-09_calendar_effects.md:23` already records a -0.54 correlation between
T-8..T-4 and T-3..T-1 returns. *Reuse:* `timed_hold` with `month_day`, multi-day hold, the NYSE
calendar in `day_filter.py`. *Cheap test:* pandas on development D1 closes, US500 only (the other US
indices are the same bet): signed return over T-3..T-1 given the sign of T-8..T-4. *Kills it:* signed
mean under 15 bp, t under 2, or opposite signs in the two halves (declare the 2017 T+2 settlement
shift before the run). Counts as the same family as F4 for multiple testing. *Prior art:* Etula et
al. 2020 "Dash for Cash"; Harvey, Mazzoleni, Melone 2025 on rebalancing; "pension rebalancing month-end".

**3. A diversified daily trend portfolio, judged as one portfolio.**
*Mechanism:* slow adjustment and hedging flows give each market a small trend premium; it only shows
across about 30 weakly related markets. Strategy 4 was run on 5 symbols one by one. *Reuse:*
`strategy/trend_following/indicators.py`, `analytics/portfolio.py`, `analytics/daily.py`,
`CostConfig.swap_r_nights`. *Cheap test:* pandas on D1 closes of all cached symbols, volatility-scaled
sign of the 12-month return, monthly rebalance, spread and swap charged. *Kills it:* net portfolio
Sharpe under 0.4 on development; more than half the profit from 3 symbols; the result needs positive
swap credits (B5). Honest prior: 2015-2021 was a weak period for trend funds. *Prior art:* Moskowitz,
Ooi, Pedersen 2012; Hurst, Ooi, Pedersen 2017; Carver (backlog I-51).

**4. Oil carry from the futures curve.**
*Mechanism:* theory of storage: a backwardated curve (scarce inventory) has paid a premium to longs,
contango the opposite. *Needs new free data:* daily front and second-month WTI settlements (EIA).
*Reuse:* the D1 path of `trend_following`, multi-day holds in `timed_hold`; financing must be modelled
from the curve, not from today's swap (B5). *Cheap test:* pandas, monthly sign of front minus second
month, next-month USOIL return including the modelled roll. *Kills it before any build:* fewer than
10 regime changes in development (too few independent bets); net ≤ 0 after a 3 % per year broker
markup. *Prior art:* Gorton & Rouwenhorst 2006; Erb & Harvey 2006; Koijen et al. 2018 "Carry".

**5. Cost side: resting limit entries for clock-based holds.**
*Mechanism:* no new edge; it cuts the cost, which is the binding limit (gross +0.01 to +0.07 R vs
cost 0.02 to 0.2 R). Rest a limit at the bid for N minutes before the entry time, go to market at the
deadline. *Reuse:* `Order.limit_fill`, `pending_limit_orders`, `tp_penetration`, `fill_probe` and
`fill_report`. *Cheap test:* the frozen F1a cell with the limit entry on development data, and a demo
fill probe with limit orders. *Kills it:* average 5-minute move after a fill goes against the order
by at least the half-spread saved (adverse selection), or fill rate under 60 %. Applies only to
cells where gross is already near cost. *Keywords:* "limit order adverse selection", "FX passive execution".

### Tips for the research process

1. **Compute the power before spending a test.** My estimate for Gotobi G1: development 413 trades,
   +0.040 R per trade, p 0.0035, so the trade sd is about 0.28 R; the test had 321 trades, standard
   error about 0.016 R. If the true edge is half the development value (0.02 R, which is what the
   test showed), "bootstrap lower bound > 0" is met only about one time in four. A fail then says
   little. Add a "minimum detectable edge at the planned sample" line to every spec; for underpowered
   cases pre-register a combined estimate (pre-sample + development + test) or a forward demo instead
   of a pass / fail gate.
2. **Run a positive and a negative control through the pipeline.** About 25 hypotheses, no pass: the
   false-negative rate is unknown. Inject a known drift (for example +3 bp in a clock window) into
   the M1 data and check the gates find it as often as the power says; run shuffled days and check
   they pass at most 5 % of the time. `data/random_walk.py` and `analytics/monkeys.py` are most of it.
3. **Filter by mechanism and by size.** Prefer ideas with a counterparty that must trade (rebalancing,
   hedging, settlement, index rules) and an effect stated in bp per event. Halve a published effect
   before the cost check (post-publication decay; McLean & Pontiff 2016). Put the "stop proposing"
   list of cost-wall §4 at the top of every harvest prompt: the research log says the harvests
   returned many families that were already falsified or not runnable.
4. **Count every look.** Screens, cells and one-time tests all go into the committed ledger (A1); the
   family-level threshold uses that count. The 792 + 660 cell screens did this well (threshold 4.0)
   and the timed-hold program set a family level of 0.01; make one such rule cover all hypotheses
   together (15 so far), not each program on its own.
5. **Fixed stop rules.** One Codex window per hypothesis; stop at the first failed gate; no rescue
   variants (already a rule); close a family after two falsifications; a "lead" expires after one
   failed independent check (F1a failed its pre-sample: close it, do not park it). Before more
   research, ask the Monte Carlo / prop tools what edge per trade the FTMO goal needs at a realistic
   trade count; an idea that cannot reach that size is not worth a build even if it is real.

---

## Verification by Opus (2026-11-11, HEAD `fba8e69`)

Each finding was opened at its file:line and, where possible, reproduced with a scratch script
(default `CostConfig()`, `_test_authorized`, tick-size comparison). CONFIRMED = reproduced or read
in code; PLAUSIBLE = consistent with the code / records but not measured; REJECTED = wrong. Line
numbers in B8, B10 moved after `0741e6a` / `fba8e69`; the findings did not.

**A) Workflow**
- A1 CONFIRMED: results live in spec, research log, HANDOFF, candidate / idea rows and cost-wall;
  `cost-wall.md:84` still says the spread proposal is "not wired in" (applied in `d0bbcd8`).
  `research/ledger.csv` does not exist yet.
- A2 PLAUSIBLE: a process judgement; `tools/time_of_day_profile.py` exists and cost-wall §1 shows
  most families died on gross < cost; the build-before-screen count was not measured.
- A3 CONFIRMED: 252 / 317 / 528 lines; `timed_hold_gates.py` also carries the energy_report and
  daily_reversal modes.
- A4 CONFIRMED: AGENTS.md:78-80 vs :82-83; AGENTS.md:165-167 vs CLAUDE.md never-idle; skill :68-69
  vs :70-78; skill :8 usage line lacks `Test=` (front matter has it); skill :18-19 vs never-idle;
  two Telegram blocks in CLAUDE.md plus the skill's.
- A5 CONFIRMED: HANDOFF is now 247 lines (after `fba8e69`), still with the 2026-11-03 state and
  closed ☑ items.
- A6 CONFIRMED: full suite at `fba8e69` 5,733 passed, 14 skipped, 4 xfailed in 571 s (green);
  slowest `test_monkeys` 30.2 s, `test_filelock` 15.2 s, `test_ts_gates` 11.6 s.
- A7 CONFIRMED with one correction: 12 worker rows; one row is "not enabled" (DeepSeek), GitHub
  Models is off in the prose, not a row. Model IDs repeated in `ai-dispatch` SKILL.md:20.
- A8 CONFIRMED: AGENTS.md "9 so far", "26 symbols"; 14 strategy folders (incl. `fill_probe`);
  README.md:35 "7 strategies".
- A9 CONFIRMED: 46 / 54 / 65 KB.
- A10 CONFIRMED: both lane worktrees clean, branches merged, both still in `lanes.json`; `briefs/`
  now 112 files.

**B) Problems**
- B1 CONFIRMED (mechanism), severity overstated: at 2026-10-06 14:00 UTC the default config uses
  the table: GBPUSD 0.00002 (fixed 0.000059), GBPJPY 0.014 (0.023), NAS100 1.45 (1.9), US500 0.56
  (0.61), XAUUSD 0.43 (0.41). But the fill report measured the under-charge against the *table*
  as much smaller than against the old fixed spread (`fill_report_2026-11-09/spread_proposal.md:22-26`):
  GBPJPY 1.4x, NAS100 1.2x (median), GBPUSD median 1.0x, US500 1.07x, XAUUSD 0.82x (over). The
  2x figures belong to the fixed spread. The table is hourly: at 21:00 UTC it is far above the
  fixed value (GBPUSD 0.00064, GBPJPY 0.2), so `max(table, fixed)` would double-count the tail.
  Medium, not high.
- B2 CONFIRMED: `_test_authorized(None, ...)` returns True; 2 of 48 grids have `[submission]`;
  the CLI runs the test unless `--dev-only`; the once-guard is keyed by the grid hash in
  git-ignored `results/research/`.
- B3 CONFIRMED for gap fade: V1 11.4 developed it on 2020-01..2026 and 11.6 ran all 36 variants
  on FTMO 2021-09..2026-09 (+13.9 R); the three tool defaults are as stated. The UNVERIFIED point
  for gap momentum: REJECTED as stated: the "quiet sideways" cells come from the strategy profiles
  on the development period (`research-log.md:294-317`) and strategy 7's rules were set on
  development data (`strategy-gap-momentum.md:46`). PLAUSIBLE milder issue: the gap momentum idea
  itself was chosen as "the opposite side of the failed gap fade" (V1 11.12), whose study saw 2021+.
- B4 CONFIRMED (no dividend handling anywhere in `src/`). The 3-4 % per year size is PLAUSIBLE,
  not checked; US500 / NAS100 / US30 pay smaller dividends too. FTMO's booking stays
  **UNVERIFIED**: the saved deal exports (`results/fill_report/deals*.csv`, 2026-10-27 / 28) hold
  only intraday buy / sell deals, no dividend or balance rows.
- B5 CONFIRMED: USOIL long +4.966 = +19.6 % per year of notional at its reference price 92.50,
  UKOIL +21.8 %; 20 positive per-lot swap entries in total (JPY-cross longs, USD-base longs,
  index shorts NAS100 / US30 / UK100, ...); price scaling keeps the sign (`costs.py:586-591`).
- B6 CONFIRMED and FIXED in `2a2122f`. First failing commit: the lane merge `47f5aff` (both imports
  enter there on the first-parent line), 29 commits before the fix. The new tick default equals
  `TICK_SIZES` for every symbol except the Binance pairs, which daily_reversal does not support.
- B7 CONFIRMED: `results/` git-ignored (`.gitignore:21`), `results/trials.jsonl` 250 KB local only.
- B8 CONFIRMED by code: spread looked up at entry (`backtest.py:477`), stored (`:526`), used for the
  short's SL trigger (`trade.py:229`) and exit fill (`:345`). Size depends on the clock (default
  table GBPUSD 14:00 0.00002 vs 21:00 0.00064); not measured on a result.
- B9 CONFIRMED, size corrected: USDCHF traded about 0.88-1.03 in 2015-21, so its commission is
  under-charged about 6-17 % (at 0.95: +15 % with `1 / price`). USDJPY at 110: -30 %, USDCAD at
  1.30: -8 % (both conservative today). Non-USD quotes (EURGBP, GER40, UK100, JP225, ...) err both ways.
- B10 CONFIRMED: HANDOFF:93-95 "not merged yet" vs :188 merged; :81-83 proposal "not wired in" vs
  :196 done `d0bbcd8`; `cost-wall.md:84`.
- Risk stubs CONFIRMED: 5 / 5 / 4 lines, only the `risk/__init__.py` docstring names them.

**C) Delete or merge**
- Risk stubs, intake remnants (`research.py:330-345`, `:1130-1136`, `pyproject.toml:18`, `[submission]`
  in `alternating_path.toml`, `london_fix.toml`), lane worktrees: CONFIRMED. Removing the
  `[submission]` handling before B2 is fixed would make those two grids test-authorized by default.
- Branches: CONFIRMED merged: `docs/v2.4e-economic-calendar`, `lane/review_h1`, `v2-chart-trades`,
  `v2-grid-merge`, `v2-live`, `v2-review`, `v2-setup` (and both lanes). `wip-a2a3-gemini` is not
  merged: one commit `98d996c` "Gemini's unfinished A2+A3 ... unreviewed".
- `orb_example.toml`, `check_gap_fade.toml`, `check_orb.toml`: CONFIRMED no test reads them (only
  the `research.py` docstring and ROADMAP name `orb_example`).
- Bootstrap spots CONFIRMED: `analytics/bootstrap.py`, `risk/bootstrap.py` (shim),
  `alternating_path_gates.block_bootstrap`, `timed_hold_gates.difference_bootstrap` /
  `date_cluster_bootstrap`.
- Spec name mismatch, archive counts (briefs 112, `docs/review/` 28 files, ROADMAP 445 lines):
  CONFIRMED.

**D) Ideas**: not verified (not to be built or screened now); duplicate check in the triage.
