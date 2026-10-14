> Reading notes, own words, made 2026-10-14 from the PDF in `00_Literature/Trading`. Part of the knowledge base: see [../README.md](../README.md). Synthesis across books lives in `../topics/`, strategy ideas in `../ideas.md`.

# Volman, "Forex Price Action Scalping" (2011) - SECOND HALF notes

Range read: text lines 6300 to end. Covers: end of Ch 11 (Range Break, Fig 11.10, book p.172-174), Ch 12 Inside Range Break
(IRB, pp.175-208), Ch 13 Advanced Range Break (ARB, pp.209-240), Ch 14 Tipping Point Technique (trade management, pp.241-280),
Ch 15 Unfavorable Conditions (trade selection, pp.283-306), Ch 16 Trade Volume (account management, pp.309-320),
Ch 17 Words of Caution (p.321-322), About the Author, Glossary (p.325+, skimmed only). Setup definitions DD/FB/SB/BB/RB are in the other half.
Ch 12-13 are mostly annotated chart walk-throughs (I read the rule-bearing parts and skimmed the figure captions).

## Overview
- Volman is a discretionary price-action scalper on a 70-tick EURUSD chart with a 20 EMA as only indicator. Entry at market on the
  break of a signal bar / signal line; bracket order 10 pip target / 10 pip server stop, but the real stop is a mental "tipping point"
  (average real stop 6-7 pip incl. spread). Target is always 10 pip, never changed.
- The second half adds: three range setups (RB already in other half, IRB inside a range, ARB after the break), the exit method
  (tipping point, trailing only after a technical feat), a trade-skip filter (unfavorable conditions: overhead resistance, round
  numbers, spikes with no buildup), and compounding position sizing (2% model).
- Almost everything is chart-reading judgment ("is there clustering/resistance between entry and target?"). Very little is
  mechanically specified; no win rate, no expectancy, no trade statistics are given anywhere in this half. The author explicitly says the edge
  is "a personal perception", not a statistical certainty (Ch 15 note, p.306). Worked examples are illustrations, not a listed sample, so
  there is NO win/loss count to extract (I looked: only anecdotal outcomes; see Ch 14 tally below).
- Stance: process over outcome, scratch fast on invalid trades, do not exit valid ones, skip 90% of the time ("observational stance 90 per cent of the time", p.283).

## Chapter notes

### Ch 11 end - Range Break, Fig 11.10 (pp.172-174)
- Range after a trend that goes sideways without pulling back = continuation; "trend equals trend" (move after range mirrors move before).
- Checklist of bullish clues (7 listed): trend up, box bottom on technical support, tight around round number, equal lows in box + a false break below,
  compressed W pattern, pre-breakout tension (a small doji), MA pushing price out of the box top.
- Do not trade the early "tease" (a poke through the barrier before the real break) even if the odds look good, to avoid training the habit of acting early.

### Ch 12 - Inside Range Break, IRB (pp.175-208)
- IRB = a small block (mini range, equal highs or lows on the break side, ideally 1-2 tiny dojis of <= ~3 pip right before) inside a bigger range, traded on the break of the
  block (signal line). Entry at market on the break. Three uses: (1) barrier bounce (block sits at top/bottom barrier, trade away from barrier,
  "boomerang"), (2) midway trade in a wide range, (3) breakout anticipation from inside the range.
- Room rule: for a boomerang trade the range must leave ~10 pip of free path after subtracting the block's own height: ranges of roughly >= 20 pip wide.
- Block width: not wider than ~5 pip; if the block is compressed it is OK for one bar to break both ends; two pre-break dojis not mandatory when whole block shows tension.
- Risk arithmetic (p.196, 182): risk in pip = height of signal bar/pattern + 3 pip (1 pip each side so the bar is taken out, 1 pip for spread).
  Example: 5 pip handle -> 8 pip loss vs 10 pip win. Stated: with +10 / -7 you do not need >50% winners; "not even six out of ten".
- Ranges 10-15 pip wide tend to expire sooner; if no decision after ~1 hour of sideways, sharpen focus (explicitly "not a rule").
- Tease and false-break traps: avoid buying the top / selling the bottom at a barrier unless there is block buildup; false break with the trend is harder to prove false than counter-trend;
  lack of follow-through for 1-2 bars after a break = break likely fails. A false-break bar is a clue to trade the opposite way, entry as close to the false-break level as possible.
- "Double pressure": enter where the losers are forced out AND sidelined players join (both order flows in your direction). Also the converse: do not trade into a spot where your side is taking profit and the other side buys in.
- Round numbers act like a vacuum/magnet; price pierces levels by several pip when bars are wild; 20-level (x.x020, x.x080 style) and 00/50 levels = support/resistance.
- Market speed reference (p.193): active European/US sessions print ~120 70-tick bars per hour (equals a 30-second chart); the quiet opening-of-Europe example had ~160 bars per 2 hours. Lunch-hour US session (from about 2.5h into the US session, can last >2h) gives highly readable ranges around round numbers that often break when traders return (Fig 12.7).
- Sizable trades/counter-trades are accepted only when overall picture favours the direction; "regard all valid setups as equal", no "safe vs less safe".
- Philosophy: losses are business costs; do not look at daily P/L or the platform P/L window while in a trade (p.277).

### Ch 13 - Advanced Range Break, ARB (pp.209-240)
- ARB = second chance entry after a range break that the plain RB did not catch. Type 1: small cluster (BB-like) hanging on/around the broken barrier, sometimes with barrier running through it; signal line of the cluster lies OUTSIDE the range. Type 2: pullback to the broken barrier zone after a powerful breakout, a signal bar forms in the zone, entry when it breaks in the original direction.
- Ranges outnumber trends "at least 4 to 1" (author estimate, p.210) -> neutral approach: pullback trades in trends, breaks/scalps in ranges.
- Barrier quality: need equal highs/lows; sloppy barriers give hesitant breaks and less follow-through; best when several tick/time frames show the same barrier.
- Awkward stop rule (p.236): if the technical stop cannot be placed within the 10 pip span, skip the trade; an obvious support/ resistance level as stop invites a stop hunt. A skipped trade stays skipped even if it would have won; review reason for skipping later, not during session (p.228).
- "Ceiling test": after a break price often returns to test the last arch of the range (the barrier). Stops go behind that ceiling, not just behind the ARB dojis (costs up to 2 pip extra, risk still ~7 pip).
- Asian session (02:00-10:00 in his chart time): ranges often > 2h with clean boundaries; sometimes thin-market trending swings (Fig 13.6).
- SB-style second break after a skipped first break is treated as a valid second chance (p.237).

### Ch 14 - Tipping Point Technique (pp.241-280) [the trade-management core]
- Tipping point = the chart price level that, if traded through by even 1 pip, makes the trade invalid -> exit at market immediately, no questions, no hope. Mental stop only (pipette/spread uncertainty makes a server stop at that level unusable); exit when a chart bar visibly takes out the high/low.
- Bracket 10/10 is a safety net for platform/internet failure only; target stays 10 pip, never moved. Stop may be moved only toward the target. Average real stop 6-7 pip; max 10.
- Initial tipping point: 1 pip beyond the setup (below the lows of the DD dojis / BB box low / signal bar low); for range-break after a squeeze, below the squeeze cluster / last arch ceiling.
  "+1 pip insurance": move the stop 1 pip further out ONLY if that extra pip lets it coincide with an earlier technical high/low (matching tops/bottoms). Math given: a wider stop need only save the trade 1 time in 15 to pay off (-1 pip lost twice vs +15 swing). If the correct technical stop is more than 10 pip away, skip the trade, do not cheapen the stop (p.259).
- Fast markets get more extra-pip insurance; slow markets can use tighter stops. Inside ranges use the tightest technical level.
- No break-even stop and no fixed "2 pip profit" stop (explicitly a "cardinal sin"): entry is a technical level that is often retested; BE exits only when a tipping point happens to coincide with entry.
- Trailing rules (the only way to tighten): (1) price must pull back, make a higher low (long)/lower high (short) AND that low must have tested prior support/resistance or the 20 EMA; (2) the pullback bar's high (long) must then be taken out by a later bar ("tipping point bar must be taken out like a signal bar") - only then is the stop lifted to the pullback low (or 1 pip beyond); (3) never trail below every minor higher low ("would cut short almost any 10 pip run"; "maybe more than half of the trades that reach target endure a serious pullback").
  Rule of thumb: he seldom exits a short while price is below the 20 EMA or a long above it; highs below the EMA (short) / lows above the EMA (long) are monitored carefully; exception when a prominent opposing double/triple top is in the path (Fig 14.9).
- Do not exit 1 pip before the tipping point is touched; do not exit a still-valid trade because of stagnation. Stagnation clusters or reversal patterns (double top/bottom, lower top, H&S) formed against the position DO count: exit when they break against you (Figs 14.13-14.16).
- If the trade is at +9 pip below strong resistance, he holds ("rare for a chart not to show obstacles"); premature scratching in routine is a habit to avoid.
- Five trade states: immediately going sour; reluctant to start; going well no pullback; classic pullback; seriously stalling.
- Re-enter if stopped out by a typical shake (false break by 1 pip) and the setup re-forms (Fig 14.10).
- Fig 14.16 shows a staged tipping point: start at the higher intermediate top, lower it after price clears the range barrier, then to the IRB box bottom, then to the break-even level after a new low is printed; two different entries on the same chart manage identically from the moment both are in ("entries do not determine tipping points, chart levels do").
- Spread arithmetic (p.258): every trade starts at -1 pip (1 pip spread); target 10 pip therefore needs 11 pip of chart travel; same distance for long/short regardless of how the spread is split.
- Trade outcomes in Ch 14 figures (anecdotal, not stats): of ~16 managed examples, mostly shown to illustrate stop placement; clearly stated losses: 5 pip (14.14 first), ~6 pip (14.15), ~1-2 pip (14.5, 14.13 IRB), small gain/loss others. Reach target mentioned for 14.1 first trade (maybe), 14.16 IRB (yes), 14.10 BB (no, stop not attacked). No counts given; do not use as statistics.

### Ch 15 - Unfavorable Conditions (pp.283-306) [skip filter]
- Method only works in "favorable market": be observational 90% of the time. Ideal is a free path >= 10 pip to target; rare, so accept some resistance but avoid: clustering price action immediately left of entry, or a stronger wall (double/triple top, range) within the 10 pip path.
- Skip list (each figure): short into round-number support that was defended 4 times; long straight into an earlier top after a non-buildup spike (spike from the low of the chart through all previous resistance = "shock", prone to full retrace); DD setup after a scribbling/clustering pullback (DD is weak, needs a diagonal or substantial pullback; BB/SB carry more tension); shorting at the bottom of a range / a bottom after a long decline (double pressure against you); setups right below a significant level where a break would hand opponents "excellent odds to counter" (Fig 15.10); trades in a tight fight around a round number where resistance and support coincide; counter-trend rallies that have not been followed by a deeper pullback (Fig 15.11).
- Rule of thumb: the more overhead resistance one can imagine, the more a weak setup (e.g. tiny DD) should be avoided; stronger setups (BB with buildup) can crack faltering resistance.
- Strong sudden one-directional move without follow-through tends to retrace 100% to its origin (p.304).
- Accept probability talk: aggressive trader can take marginal trades if 5 pip stops lost twice per 10 pip win still break even (p.305) (note: only 33% win rate required if risk 5 vs reward 10 with the 1 pip spread ignored).
- Conservative vs aggressive: in most situations both make same decision; if unsure choose conservative mode.
- Scan for levels when no trade is in sight (keeps neutral view).

### Ch 16 - Trade Volume (pp.309-320)
- "2 percent model": risk at most 2% of account on a 10 pip stop (1% for beginners, raise slowly 1.0 -> 1.1 -> 1.2 ... as proficiency grows). Units = balance x risk% x (100 / stop pips) e.g. $5000 x 2 x 10 = 100,000 units (formula factor 10 for a 10 pip stop). EURUSD: 1 pip on a 100k lot = $10. Leverage needed 30:1-40:1 for a full lot on a $5k account.
- Recompute volume once per day (end of session/before next), not intra-trade; reduces size after losses automatically (compounding factor works both ways).
- Compounding illustration: 5 pip/day for 200 days on a $10k account with 2% model: flat size $30,000 vs compounded $73,160; $5k -> $36,580 after 200 days at +1%/day; losing 5 pip/day for 200 days leaves $669.90; 10 pip/day compounded 2%/day takes $2k above $1m in ~314 days (author warns this is fantasy). 232 days to 10x at 5 pip/day (daily +1%).
- Do not withdraw profit early if undercapitalised; trade tiny until consistently profitable; "lower your volume until you just don't care".
- Note for us: this is a sizing description in R terms: a fixed fractional risk per trade (1-2% of the stop), updated daily. FTMO needs <= ~0.25-0.5% per trade for 5% daily / 10% total limits; his 2% is far too much for a prop account.

### Ch 17 - Words of Caution (pp.321-322)
- No scientific evidence for trading rules; any method is a personal snapshot, future may defy it; study/test on historical and current charts for countless hours; trade small first; if still affected by losses reduce size; if unsure choose the conservative mode.

## Topic tags
- trend: 20 EMA only as visual aid / pullback guide ("guides us 90 percent of the time"); with-trend breaks harder to fake; trend equals trend after sideways flag; ranges outnumber trends ~4:1 (author claim).
- breakout: RB/ARB/IRB all trade breaks of a tight block/signal line with pre-break tension (1-2 tiny dojis, equal highs); tease and false-break filters; follow-through within 1-2 bars; second-chance entry after a skipped break.
- mean-reversion: IRB barrier bounce/boomerang inside ranges >= ~20 pip wide; false-break reversal; 100% retrace of a spike without follow-through.
- momentum/oscillators: none.
- patterns: block/box, double top/bottom, H&S, cup-and-handle, bull flag, squeeze; all discretionary.
- intraday/sessions: no time filter as rule. Descriptions: Asian (02:00-10:00 chart time) long ranges; US lunch hour congestion around round numbers; avoid news releases (spread mark-up and 1-minute spikes; earlier chapter); 160 bars/2h slow vs 120 bars/h fast on 70-tick.
- seasonality/time: ranges of 10-15 pip tend to expire after ~1 hour; not a rule.
- volatility: stop sizing from signal bar height + 3 pip; 10-pip target assumed achievable only with free path; speed of market changes extra-pip insurance.
- stops-and-exits: tipping point system; no break-even; trail only after technical feat; scratch on a 1-pip violation; fixed 10 pip target; server stop 10 pip as disaster stop; skip if technical stop > 10 pip away.
- position-sizing/risk: 2% (or 1%) model, daily recalculation, compounding, grow risk gradually, drop size when emotionally affected.
- testing-and-robustness: author gives no statistics; says edge is personal perception; recommends backtesting by eye on history. (A rule-based version of his method has never been validated by the book.)
- costs/execution: 1 pip spread = 10% of the target and ~14-17% of a 6-7 pip risk per trade; breakeven win rate for +10/-7 is about 41% (with the spread already in the 7); 11 pip chart travel for a 10 pip target; brokers' spread mark-ups during news are a major danger.
- psychology/discipline: commitment to pull the plug; judge decisions by information before, not by outcome; do not predict how a setup will present; no bias; being on the sidelines is "holy ground"; do not look at P/L in trade; analysis after the session, not during.
- portfolio/diversification: none (single pair EURUSD).

## Testable ideas (our data: M1 only, FX/gold/indices, spread+commission+swap modeled)

M1-equivalent of the 70-tick chart: an active EURUSD session prints ~120 70-tick bars/hour = 1 bar per 30 s, so one 70-tick bar ≈ 0.5 M1 bar;
his "doji <= 3 pip" and "10 pip target" are measured in bar-range units. Approx. (my estimate, not from the book): EURUSD M1 ATR(14) in active hours ~3-5 pip, so
a 10 pip target ≈ 2-3 M1 ATR, a 6-7 pip stop ≈ 1.5-2 M1 ATR. Use M1 with the ATR-based units below, and M5 as a robustness variant.

### Cost survival of 10/20-pip brackets (estimates; verify spreads in histdata/FTMO feed)
- Volman's own economics: spread/target = 0.10; spread/(avg stop 6.5) ≈ 0.15 R paid per trade; needs ~41% win rate at 10:7 (breakeven incl spread cost).
  Scale the tick economics by requiring: target >= 10 x spread and target >= 2.5 x M1 ATR(14), stop = signal bar height + 3 "pip" units (1 unit = 1 spread-equivalent... see below).
- GBPUSD: typical spread ~1.0-1.5 pip (FTMO ~0.8-1.2 + commission), M1 ATR ~4-6 pip in London/NY. 10 pip target = 8-10x spread -> borderline OK; use target >= 12-15 pip (2.5 ATR) so spread <= 10%.
- GBPJPY: spread ~2-3 pip, M1 ATR ~6-10 pip. 10 pip target = only 3-5x spread = ~25% cost -> fails; need target >= 25-30 pip (3 ATR) to get back to 10%.
- XAUUSD: spread ~$0.20-0.35 (20-35 cents), M1 ATR ~$0.8-1.5. Target >= $2.5-3.5 (2-3 ATR) keeps spread <= 10%; in "pip" terms of his 10 pips (= $1.00 if a pip is 0.10) the target would be ~ 3-4x spread = fails.
- General rule to carry over: define target T = max(2.5 x M1_ATR14, 10 x spread), stop S = signal-bar range + 2 ticks + spread, and require S <= 0.8 x T (the 10/7 relationship). Scalp trades are only viable on M1 if gross expectancy per trade > ~0.15 R; our strategies 1-3 died partly on costs, so test cost-sensitivity explicitly (run gross vs net).
- Swap: all ideas are intraday, flat before 17:00 NY rollover -> no swap.

### ★ Idea A - Squeeze block break with ATR-based pre-break tension (RB/BB/IRB core)
- Detect a block: >= 4 bars in a narrow range (<= ~1.5 x M1 ATR total height, "block <= 5 pip" analog) with >= 2-3 equal highs (within 1 tick) on one side; last 1-2 bars before the break are tiny (range <= 0.3-0.5 x ATR, "dojis"); trade the first M1 bar whose high (low) breaks the equal-level + 1 tick, in the direction of the 20 EMA slope/price side (EMA(20) on M1 as direction filter).
- Stop = block (or last arch) extreme + 1 tick + spread; target = 10-pip analog (fixed 1R-1.4R, e.g. 1.43R target for 10:7); scratch exit rule below. Time stop: if not at target within N bars, exit at close.
- Source: Ch 12 (IRB), Ch 11 (RB), Ch 14.3 (last arch). Claimed evidence: none (illustrative charts). Fit: possible on M1 for XAUUSD/NAS100/US500 where spread/ATR is small; poor on GBPJPY with a 10-pip scale. Differs from failed 1-3: no SMC session/liquidity, no FVG/OB, no single-candle trend filter; entry is volatility-compression (squeeze) + equal-level break.

### ★ Idea B - Tipping-point exit module (reusable across any entry)
- Initial stop at the technical level 1 tick beyond the setup; no break-even; trail only when (i) a pullback low/high forms that tested prior level or EMA, and (ii) a later bar takes out the pullback bar's high (low) -> lift stop to the pullback extreme; exit at market on first bar that trades through the stop; fixed target.
- Test as an exit overlay on strategies 2/3 entries and on a random-entry baseline to separate exit edge from entry edge; compare against fixed 1R stop and against ATR trailing and break-even variants (Volman claims BE and tight trailing hurt; testable).
- Source: Ch 14. Evidence: none quantitative. Fit: good (pure OHLC, no lookahead if the trailing trigger uses closed bars), but small expected gain; interesting for confirming/refuting "no break-even, trail only after structure" claim.

### ★ Idea C - Skip filter "free path to target" (resistance-between-entry-and-target filter)
- For every candidate entry (any strategy), compute distance to nearest opposing swing extreme/cluster (equal highs lows, prior day/session high-low, round number) within the last N bars; skip if it lies within 1.0 x target distance; skip if the setup follows a spike (>= k x ATR in <= m bars with no consolidation, "non-buildup") into a prior extreme.
- Source: Ch 15. Author's claim: majority of skipped trades are low odds; no stats. Test on our existing strategies 2-4 entries: does the filter raise net R? Cheap to implement with the swing detector. Differs: acts as a filter, not as an entry.

### Idea D - Round-number magnet/barrier (00/50/20-level) as target/skip layer
- On FX/gold: levels at x.xx00, x.xx50 (and 20/80 sublevels); avoid entries within 1 target of a level in the direction of trade; or trade fade/break retest. Source: Ch 15, 12. For XAUUSD use $10/$5 levels; NAS100 100-point levels. No evidence; cheap to test as an overlay.

### Idea E - ARB / breakout-retest second entry
- After a break of a range barrier (range: >= 1h of equal highs/lows, width 10-40 pip), wait for pullback into the barrier zone that holds (does not close back inside), then enter on break of the signal bar's extreme in the original direction; stop beyond the last arch ceiling (inside range) not just the signal bar. Source: Ch 13/14.7. Fit: uses Asian/lunch ranges, intraday; differs from strategy 1 (session zone) in that no sweep/FVG logic is used. Note related to session-range break testing; Asia range breakout on London open is a natural M1 test.

### Idea F - Fixed-fractional daily-recomputed risk with prop limits (not a signal)
- Risk% per trade recomputed daily from balance: for FTMO use 0.25-0.5% and a daily stop (e.g. stop after -2% or N losses) - Volman has no daily loss rule; he reduces size when emotional. Source: Ch 16. Belongs in risk/ module; Monte Carlo of R-lists with daily resizing vs per-trade resizing to check the "double function" claim.

Most promising: A, B, C (marked ★); D and E are cheap overlays.

## Warnings / pitfalls
- No numbers: no win rate, no expectancy, no sample, no cost-adjusted P/L given. All claims are discretionary and survivorship-biased (author-selected charts); must not be assumed to carry an edge.
- Method relies on tick-chart bar formation (activity-based bars) and human reading of "pressure"; M1 time bars and rule-coded detection will behave differently (equal highs on 70-tick bars vs 1-minute bars; tick bars shrink in quiet hours automatically, M1 bars do not -> adapt thresholds via ATR).
- 1 pip spread is 10% of his target; broker markups during news can reach 10 pip (earlier chapter) -> filter news/rollover; our data are M1 mid/bid candles (no tick spread) so use a time-varying spread model.
- Stop is mental and exits are manual at market: slippage not modeled by the author; a simulation must fill exits at bar close/next open or the stop price plus slippage, SL-first inside a bar.
- Intrabar order on M1: his tipping point exits trigger when a bar "visibly" trades through the level; with M1 bars the stop and target may both be inside one bar -> SL-first conservative rule applies.
- Compounding illustrations are best-case; 2% risk is prohibited by prop-firm drawdown limits.
- Author's own caution: past may be defied; edge is perception; need hundreds of hours of testing; lower size when affected by losses.
