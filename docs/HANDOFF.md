# Handoff

Read first in every session; rewritten at every `End.` (about 60 lines, current state only; history
in git, results in `research/ledger.csv`, plan in `docs/ROADMAP.md`).

## Where things are (2026-11-11, `End.` of the review follow-up session)

- **Repo:** branch `v2-6-research` (pushed); `main` is behind, merge only on the user's word. No lane
  worktrees; local branches `main`, `v2-6-research`; tag `archive/wip-a2a3-gemini` keeps Gemini's
  unreviewed WIP. Remote branches on GitHub were not touched.
- **Review 2026-11-11** (`knowledge/reviews/2026-11-11-fable-review.md`, verdicts appended; framework
  `...-fable-research-framework.md`) done per ROADMAP V2.10: research runner test is opt-in (`--test`);
  gap fade's one-time test struck (test period already used in V1); cost fixes B5 (no positive swap
  credit), B9 (USD-base commission at the trade's price), B1 (spread table x live ratio: GBPJPY 1.40,
  NAS100 1.12, US500 1.07), B8 (a short's spread follows the managing candle); golden lists regenerated
  per fix; dev reruns: no verdict changed (`knowledge/research/reports/2026-11-11_cost_fixes_old_vs_new.md`).
- **One ledger:** `research/ledger.csv` (42 rows: every strategy, hypothesis, screen, spec and new card;
  rules in `docs/research-runner.md` › Ledger). Trial log copied to `research/trials.jsonl` at `End.`.
- **Ideas recorded, UNTESTED:** I-67 conditional month-end sign (F4 family), I-68 oil carry (parked,
  needs EIA data), T-20 resting limit entries, I-51 judged as one portfolio, CAP follow-up on pre-sample.
  F1a is closed (lead expired after its failed pre-sample check).
- **Harvest tooling:** `tools/harvest.py` + skill `idea-harvest` + `research/harvest/known_families.csv`.
  Pilot stopped: the known-answer canary came back empty in 15-27 s at Codex terra low / medium / write
  (likely no web access in this dispatch path; its family was also in the skip list).
- **Rules set by the user today:** per-mode rule (Continue.Research decides and records, elsewhere stop
  and ask); one Telegram rule; model IDs only in `docs/agent-routing.md`; screen first, power line, stop
  rules, controls, count every look (`continue-research`); lane merge ends with `lanes remove`.
- **Tests:** full suite 5,643 passed, 14 skipped, 4 xfailed (9 min 47 s); ruff clean.
- **Uncommitted, not Opus's:** `src/backtester/tools/notify.py` (hook trace log lines); the user decides.

## Accepted / decided by the user (do not ask again; older ones in git history)

- 2026-11-11: Opus's picks on the review list ("Go with your picks"): B1 / B5 / B8 / B9 with the stated
  numbers (NAS100 applied at the measured 1.12), B3 strike, deletions (lanes, merged branches, wip
  tagged), ideas D1-D5 recorded, process tips folded in, F1a closed, harvest skill built + pilot.
- 2026-11-11: harvested ideas without a mechanism are parked, not dropped; one ledger for everything.
- 2026-11-09 / 10: see git history of this file (swap scaling, gate 7 tolerance, multi-day holds in
  scope, Sonnet only for small work, never idle, Telegram on > 5 min waiting).

## Open (needs the user)

1. One-time MT5 tests still pre-registered: strategy 4 on GBPJPY; gap momentum in quiet sideways
   markets. Only on your go.
2. **B4 dividends:** no dividend handling in the engine; FTMO's booking is unverified (saved deal
   exports hold only intraday deals). Start MT5 and Opus runs a read-only export of all deal types
   since 2026-11-02, or approve one free web lookup of FTMO's dividend rule.
3. **GBPUSD spread:** the table fits the median (1.0) but the live mean is 2.18x the table (Asia /
   rollover tail). Raise the table x2.18 (14:00 UTC 0.00002 -> 0.000044)? Not applied.
4. **Harvest web access:** a one-line probe of Codex web search (or Gemini) before any batch; then
   rerun the pilot with a canary whose family is not in the skip list.
5. Gate 7's 21:00 UTC rollover window vs MT5's 20:55 start (low priority); stressed-cost p90 refresh
   with fill runs 3 + 4; your check of data fixes 13.12-13.18.

## Next step

1. **Multi-symbol step 1b** (`docs/design/multi-symbol.md` › Delivery 1b; Codex sol), then build and run
   the five pre-registered lead-lag strategies (14 `us_close_de_open` first), development only.
2. Review items left (ROADMAP V2.10): A3 one gates tool from a `[gates]` table (Codex sol), A9 results
   out of the specs into the ledger (terra), shrink the three slowest tests (terra).

## First prompt for the next chat

`Continue.Code` for multi-symbol step 1b (answer Open 2-4 when convenient), then `Continue.Research`
(Test=manual) for the lead-lag strategies.
