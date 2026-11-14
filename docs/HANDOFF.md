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
- **Uncommitted, not Opus's (the user decides):** `src/backtester/tools/notify.py` (hook trace log lines);
  `CLAUDE.md`, `.claude/skills/continue-research/SKILL.md`, `.claude/skills/idea-harvest/SKILL.md` (new
  `Mode=manual|auto` rules, appeared during the 2026-11-14 session).

## Accepted / decided by the user (do not ask again; older ones in git history)

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

## Next step

1. From about **2026-12-02**: `python -m backtester.tools.crypto_carry --update --forward`, commit
   `research/forward/crypto_carry.csv`, report the first forward week (2026-11-16..22).
2. Research: the free-data idea space looks exhausted for now (four harvest batches, one screen). Best options:
   a new free data source (e.g. CFTC COT for positioning ideas, a download needing the user's go), or
   `Continue.Code` on V2.10 (A9 deferred; two-leg 2b when a pair idea survives a screen).

## First prompt for the next chat

> Read `docs/HANDOFF.md`. Then propose, in max 10 lines, the next research or code step (Strategy 19 forward log
> from about 2026-12-02; new free data source vs `Continue.Code`), with your pick, and start it after my ok.
