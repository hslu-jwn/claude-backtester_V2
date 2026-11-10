# Strategy 13: daily reversal (PRACTITIONER)

Status: specification and implementation only; **no grid run, no pre-registration result,
no performance claim**. Registry integration belongs to the coordinator.

## Hypothesis and evidence

Failed daily breakdowns followed by recovery may trap sellers and precede a reversal.
E8 also mirrors the hypothesis for shorts; CAP is long only. Related RSI(2) index mean
reversion was already falsified in `strategy-timed-hold.md` > Hypothesis 10. These setups
use failed breakdown patterns followed by stop-level triggers, rather than RSI thresholds;
they remain related reversal hypotheses, not independent evidence of an edge.

Source: Michael Tan, *Technical Strategies* (2002), reproducing Connors (1998):
https://michaeltanphd.com/wp-content/uploads/2021/02/technicalstrategies_2002.pdf.
The harvest/brief cites pp. 26–28; the currently served 27-page PDF places E8 and CAP on
PDF pages 22–23 (zero-based 21–22). Source inspection confirmed the patterns; the index
adaptation, tick offsets, timing and fixed exits below are this experiment's rules.
Read-only idea record: `knowledge/research/reports/2026-11-10_idea_harvest_broad.md`, ideas 2–3.

## Cash sessions and information

Build daily OHLC incrementally from closed M1 candles, whose **close times** lie in
`(cash_open, cash_close]`, matching timed_hold's session convention. Time is stored in UTC;
clocks use ZoneInfo and each city's DST.

| Symbols | Zone | Cash open–close |
|---|---|---|
| US500, NAS100, US30 | America/New_York | 09:30–16:00 |
| GER40 | Europe/Berlin | 09:00–17:30 |
| UK100 | Europe/London | 08:00–16:30 |
| JP225 | Asia/Tokyo | 09:00–15:00 |
| AUS200 | Australia/Sydney | 10:00–16:00 |

Weekends are excluded. A daily pattern bar requires the first minute closing at open+1m
and the exact session-close minute. Missing either boundary resets daily history, E8
candidates and pending entries and records `incomplete_session`. Invalid/nonpositive
prices record `invalid_candle` and invalidate that session. Candles inside the session
are aggregated as received; full interior-minute coverage and entirely absent sessions
must be checked against exchange calendars by the gates tool. No synthetic daily bars.

Session counters count observed weekday cash-session dates, including partial dates;
absent holidays/weekends do not count. An entirely missing trading date is indistinguishable
from a holiday without an exchange calendar: it is an integrity failure for the external
gate, not permission to accept a delayed exit. Daily pattern numbering requires consecutive
valid observed bars; a partial observed session breaks that sequence.

## E8 setup

Long rules (shorts mirror using Direction, exchanging highs/lows and inequalities):

1. Day 1 low is strictly below all previous seven daily lows.
2. Day 2 high is strictly above day 1 high.
3. The **first** of days 3–6 whose low is strictly below day 2 low confirms the setup
   only at its cash-session close. An individual pattern can confirm only once.
4. After confirmation place a buy trigger one tick above day 2 high, stop one tick below
   day 2 low. Valid during the next four observed cash sessions, including the fourth close.
   No entry on the confirmation day. Reject nonpositive risk.

Track overlapping candidate sequences until confirmation or day 6. At most one pending
setup per direction per symbol: a newer confirmation replaces the older pending setup.
If several sequences confirm on the same close, the sequence with the latest day 1 wins.

## CAP setup

Long only: signal low strictly below the previous nine lows; high-minus-low range strictly
larger than each previous nine ranges; nonzero range; close >= low + 0.75 × range (top
quarter inclusive). After its close, buy trigger one tick above signal high, stop one tick
below signal low. Valid during the next two observed cash sessions, including the second
close. New qualifying signals replace an older long pending setup.

## Execution and exits

**Opus decision 3 (2026-11-10) supersedes the brief's original stop/worse-open fills.**
No engine change: on the first later cash-session M1 candle with high >= long trigger
(low <= short trigger), emit a market Order at that candle's **close**, also for a gap
opening beyond the trigger. Standard engine spread, commission, slippage and tick rounding
apply. This is a stop-trigger emulation, not a true stop-order fill. Although the decision
calls it conservative, a retracing trigger candle can close at a better price; conservatism
is not mathematically guaranteed. No fills at the stop level or gap open are claimed.

Consume a touched pending setup even if rejected. Require the close strictly beyond its
stop in the profitable direction; additionally skip a trigger candle that touched the stop
(unknown intraminute ordering). If both pending directions trigger in one candle, cancel
both and skip the trade (Opus decision 2). Enter at most one position per symbol, clear
all pending setups/candidates on entry, and arm no new setup while a position is open
(decision 4). Engine rejection callbacks release the occupied slot; no retry of that signal.

Risk R is the absolute distance between the actual close-price entry and fixed stop.
Target is entry + direction × target_r × risk, or no target with `target_r = 0.0` (TOML's
numeric encoding of **none**). No session break-even, no trailing, no partial exits.
SL and TP are engine-managed on subsequent candles, including outside cash hours;
SL wins when both are touched. Targets/stops take precedence over the timer.

**Opus decision 1:** fill session = zero. Count five full subsequent sessions with default
`hold_sessions=5`; exit at the fifth session's cash close. If that exact candle is missing,
request exit at the first available later candle, record `missing_exit_candle`, and fail
the integrity gate. End-of-data liquidation before the scheduled exit is censored and must
fail the gate. Holds remain open across weekends; the shared engine charges side-specific
swap at 17:00 New York, including the symbol's triple weekday, with standard price scaling.

## Frozen experiment and gates (before any run)

Four pooled cells, a single parameter set across all seven symbols:
`setup={E8,CAP}` × `target_r={2.0,none}` × `hold_sessions={5}`.
Primary cell: E8, target 2.0. Do not choose per-symbol parameters. Diagnostics off.
Develop only before 2021-09-14; the one-time MT5 holdout needs separate user authorization.
No grid is run in this task. The grid file is an input draft, not a completed pre-registration.

All gates are conjunctive, strict >0 unless specified:

- Pooled total net R positive under normal and doubled spread/commission/slippage/swap
  costs; double cost amounts while preserving trading rules and use a complete rerun to
  capture cost-filter/ask-side effects. Report trade counts for both runs.
- Both chronological development halves net positive (fixed midpoint of the development
  interval, not the midpoint of the trade list; attribute by entry timestamp).
- At least four of seven indices net positive, with all seven covered.
- Remove the five best pooled **entry dates** (UTC, rank their total net R); remaining net
  R positive. Remove whole date clusters across symbols, not five individual trades.
- Pooled bootstrap lower 2.5% quantile of mean net R positive. Gates tool must resample
  pooled entry-date clusters (preserving cross-index dependence), seed 13, 10,000 draws;
  compute per-trade mean in each resample. Report sample and cluster counts.
- At least 80 pooled trades per cell under normal costs.
- Integrity: no missing exit candle, invalid candle, incomplete signal session affecting a
  setup, missing exchange-session data or end-of-data censored positions; enforce exchange
  calendar and interior-minute coverage before scoring. Unknown integrity = gate not passed.

Report long/short separately and by index and half, explicitly discussing bull-market drift
in 2015–2021. CAP has no short leg. Report all four cells and all trial counts regardless
of outcome; do not promote a secondary cell by silently replacing the primary.

### Gates tool / coordinator integration still required

The standard research runner does not implement this entire gate set. It needs normal and
stressed reruns, pooled net/halves/index/date-removal tables, date-cluster bootstrap,
directional splits, exchange-calendar coverage and censored-trade checks, plus serialized
`integrity_records()` (also exposed by `session_records(run_end)`). Do not interpret the
standard runner's verdict as passing these gates. Validate financing and tick metadata
before running; the harvest warned about historical index financing scaling.

Coordinator registry imports: `DailyReversalConfig` from `daily_reversal.config`,
`DailyReversal` from `daily_reversal.strategy`; entry:
`StrategySpec("daily_reversal", "Strategy 13 · Daily reversal (Connors)", DailyReversalConfig, DailyReversal)`.

## Assumptions for review

Decisions 1–4 above are the supplied Opus decisions dated 2026-11-10. Additional minor
conservative choices authorized by decision 4: first qualifying day 3–6 consumes a sequence;
same-close ties prefer the latest day 1; consume rejected touches and cancel both crossed
directions; skip any trigger candle touching its stop; require both daily boundary candles;
reset incomplete history instead of bridging it; observed-session counters require external
calendar integrity checks. Entirely absent dates cannot be diagnosed from a SeriesView alone.
Pending triggers are also cancelled immediately when a session's first observed candle is
later than open+1m; skip entries for that partial session.
No new hypothesis-changing trading rule was inferred. Numeric zero means no target for
compatibility with the existing grid parser. Tick defaults come from shared `TICK_SIZES`;
configured symbol tick metadata overrides that default unless an explicit strategy tick is set.

## Amendment (Opus, 2026-11-10, before any result existed)

The first development run stopped at load time ("Replay needs at least one candle"): US30 has no candles
before 2019 (MT5 from 2019-02, no histdata), as in the timed_hold grids. US30 is dropped; the pool is 6
indices (US500, NAS100, GER40, UK100, JP225, AUS200) and the breadth gate becomes **at least 4 of 6**
indices net R > 0. Everything else unchanged.
