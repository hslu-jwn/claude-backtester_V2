# Handoff

Read first in every session; rewritten at every `End.` (about 60 lines, current state only; history
in git, results in `research/ledger.csv`, plan in `docs/ROADMAP.md`).

## Where things are (2026-11-14, `End.` of the Binance futures research session)

- **Location:** `X:/Daten/02_Projekte/01_Laufend/backtester-claude/backtester-claude_V2`; Claude's memory notes moved
  to the new project key (7 files), no settings point to the old path.
- **Repo:** branch `v2-6-research` (pushed); `main` is behind, merge only on the user's word. No lane worktrees.
  Full suite 5,963 passed, 14 skipped, 4 xfailed (`-n 8`); ruff clean.
- **Data:** Binance USD-M cache now 37 perps (BTC, ETH + 15 listed by 2020-02 + 20 listed by 2020-08), M1 + taker flow
  + funding, 2020 to 2026-10/11 (`binance_download --klines`, 11 GB). EOS prices end 2025-05-21 (its funding file
  continues as a constant placeholder); OMG and SXP delisted 2025. Cache day files are now fsynced before the rename
  (a hard restart had left 52 damaged SXP files; repaired, full scan clean).
- **Research 2026-11-13/14 (Binance; every look in the ledger, 120 rows):** I-72 funding-settlement drift killed
  (+2 bp vs 10 bp cost); I-73 cross-sectional funding carry: development killed on t (1.30), one-time test on
  2021-09..2026-10 **passed** (+112 bp/week, t 2.93) but the pre-registered **replication on 20 unseen perps failed**
  (+63 bp/week, t 1.05; price part +35 vs +103, funding carry held); HV-T0020-3 funding-extreme fade untestable
  (122 independent clusters); I-75 weekly crypto reversal killed (-147 bp/week; large perps show momentum).
  Harvest batches 10-13 + canary check (38 tasks): nothing screenable except I-75; I-74 hedger reversal carded, below cost.
- **Strategy 19 crypto carry** (`docs/strategy-crypto_carry.md`): research tool built (`tools/crypto_carry.py`,
  `strategy/crypto_carry/book.py`, golden identical to the screen); kept as **forward paper log only**.
- **Harvest routing:** ACAD / CB tasks on Codex terra **high** (canary check 2026-11-14: medium missed the
  known-answer paper twice, high and sol found it); `harvest check` needs the Avast CA bundle (skill note).
- **Rules changed 2026-11-14 (side session, `aeffc3c`):** `Mode=manual|auto` replaces `Test=` (CLAUDE.md, skills
  `continue-research`, `idea-harvest`); re-read them on resume.
- **Uncommitted, not Opus's:** `src/backtester/tools/notify.py` (hook trace log lines); the user decides.

## Accepted / decided by the user (do not ask again; older ones in git history)

- 2026-11-14: crypto split (develop 2020-2023, test once 2024+, wider perp universe incl. delisted) for crypto families
  with no look yet (`docs/research-runner.md` › Periods).
- 2026-11-14: everything of this session accepted at `End.`; Strategy 19 forward paper log only after the failed
  replication; replication download of 20 perps; Strategy 19 spec (R = 1,000 bp risk unit without a stop, research
  tool, forward log from 2026-11-16); I-73 one-time test; fsync fix; harvest batches 10-13 and the canary check.
- 2026-11-13: 15 more Binance perps (klines + funding); challenge path simulator; data fixes 13.12-13.18; rollover
  fixes; factors GBPJPY 1.09 / GBPUSD 1.38; spread table option A; no paid futures data; Binance futures direction.
- 2026-11-12: pytest-xdist `-n 8`; one research loop at a time; always propose next steps; auto mode; futures venues
  allowed (futures prices + futures cost model, never CFD prices minus swap).

## Open (needs the user)

1. One-time MT5 tests still pre-registered: strategy 4 on GBPJPY; gap momentum in quiet sideways markets.
2. **B4 dividends:** send `docs/ftmo-dividend-question.md` to FTMO support; Opus adds the rule test-first.
3. **GBPUSD 2020-21 placeholder spreads** still in the table; drop them like the seven FX symbols? Changes a default.
4. **Strategy 19 forward log:** a monthly scheduled task (`crypto_carry --update --forward`) needs your go;
   otherwise Opus runs it by hand from about 2026-12-02. Kill after 52 weeks: net <= 0 or drawdown worse than -6 R.
5. **Crypto cross-sectional momentum** (Liu, Tsyvinski & Wu 2022): seen mirrored in I-75's development data, so only
   a pre-registered one-time run on 2021-09..2026-10 would be fair. Only on your go.
6. Low priority: stressed-cost p90 refresh; USDCHF early 2015 borderline data.
7. **(auto run 2026-11-14) Strike Open 1?** Both parked MT5 tests look spent (V1 ran strategy 4 on GBPJPY 2023-26;
   gap momentum ran on MT5 2021-26), like gap fade in review B3. Opus did not run them (research log, auto decision 3).
9. **(auto run 2026-11-14, Fable row 20) Stop rule for signal research:** after K = 10 more falsified screens with no
   pass, goal-1 signal research pauses and effort goes to prop mechanics, forward logs, combining streams and code.
10. **(Fable idea universe 2026-11-15) Count test-period uses:** from the 5th one-time test on the same test period,
    require t >= 3.0 instead of 2.0 (`knowledge/reviews/2026-11-15-fable-idea-universe.md`). Changes a rule.
11. **(Fable 2026-11-15) Free-tier account** for US share minute bars (creating an account is yours), and a go for a
    scheduled daily collector of retail positioning data (FB-284; a standing scheduled task).

## Next step

- **Idea backlog (2026-11-15):** `research/idea_backlog/2026-11-15-fable-ideas.csv` (335 ideas, 22 families; 93 at
  priority 1-2) with the framework and work order in `knowledge/reviews/2026-11-15-fable-idea-universe.md`.

0. **I-78 weekly taker-flow sort on all Binance USDT perps: one-time test PASSED** (2026-11-14; +147 bp a week, t 3.76;
   about half is pump capture in small perps, ~+56 bp a week without the tails). Goal 2 only (not on FTMO).
   **Strategy 20 built 2026-11-15** (`docs/strategy-crypto_flow.md`, `tools/crypto_flow.py`); forward log from
   about 2026-12-02 with Strategy 19: `python -m backtester.tools.crypto_flow --update --forward`. Next research:
   a slippage / position-limit realism check.

1. From about **2026-12-02**: `python -m backtester.tools.crypto_carry --update --forward`, commit
   `research/forward/crypto_carry.csv`, report the first forward week (2026-11-16..22).
2. **Auto run 2026-11-14 (research log, auto decisions 1-8):** Fable directions list (43 rows), FTMO pass map and
   power budget map (goal 1 needs ~+0.05 R net at ~300+ trades a year = ~2.5-5 bp gross per daily event), I-76
   killed, I-77 carded below cost, ideas triage, FTMO venue facts (59 share + 30 crypto CFDs), harvest batch 14
   empty. Crypto split adopted by the user (2026-11-14); next: Fable rows 9 / 21 on the wide universe (I-78..I-80).
3. Research (before the auto run): the free-data idea space looked exhausted (four harvest batches, one screen). Options were:
   a new free data source (e.g. CFTC COT for positioning ideas, a download needing the user's go), or
   `Continue.Code` on V2.10 (A9 deferred; two-leg 2b when a pair idea survives a screen).

## First prompt for the next chat

> Read `docs/HANDOFF.md`. Then propose, in max 10 lines, the next research or code step (Strategy 19 forward log
> from about 2026-12-02; new free data source vs `Continue.Code`), with your pick, and start it after my ok.
