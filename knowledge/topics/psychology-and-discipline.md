# Psychology and discipline

Sources: D = Douglas *Trading in the Zone*; H = Hougaard *Best Loser Wins*; K = Kaufman.
Mostly not backtestable. Turned into execution and risk rules where possible.

## Probability mindset (Douglas)
- Each trade's outcome is random; an edge shows only over a series, like a casino (D ch.7).
- Five truths: anything can happen; you don't need to know what happens next; wins and losses are
  randomly distributed; an edge is only a higher probability; every moment is unique (D ch.7).
- Seven principles of consistency: identify edges objectively, predefine risk, accept it, act
  without hesitation, take profits systematically, monitor your own errors, never break the rules
  (D ch.11).
- Rigid in rules, flexible in expectations (D ch.7).

## Execution rules derived from the books
1. **Take every signal** the rules define; picking and skipping breaks the sample (D ch.7; H's
   twenty-trades exercise; K p.1011: selective trading and overrides ruin consistency).
2. **Predefine risk** on every trade; the stop comes from structure, the size from the risk budget
   (D ch.11; H; K p.1032).
3. **No overrides:** no manual exit to "punish the market", no moved stops (D ch.7). Trade exactly
   the tested rules (K p.980).
4. **Mechanical first:** trade a precise system until execution is effortless before anything
   discretionary (D ch.11, three stages).
5. **No streak behaviour:** no size-up after wins (euphoria), no skipping after losses (fear)
   (D ch.3, 5). Hougaard: size up only *within* a winning trade, never to recover a loss.
6. **No black boxes or extra variables** outside the edge definition; they make it impossible to
   learn what works (D ch.8; K p.1011).
7. **Don't stop after three losses** unless ill or emotional (H); do not invent a new rule after a
   shock loss (K p.951-953).

## Hougaard's mindset points
- 80-90 % of retail CFD clients lose because they hope on losers and fear on winners: they cut
  winners, hold losers, add to losers and avoid stops. Do the opposite (H).
- Assume you are wrong until the market proves you right; be small when wrong, big when right (H).
- Loss aversion: a loss feels about 2.5× as strong as an equal gain (H, quoted study).
- Process over outcome; review every trade plotted on a chart; keep a "Book of Truths" split by hour,
  weekday and holding time (H). → idea I-22

## Why this matters for an automated backtester
- The backtester already "takes every signal" and never moves stops. The psychology lesson for us is
  about **process**: don't tweak rules after a bad stretch, don't cherry-pick variants, use one
  pre-declared rule set per test (see [testing-and-robustness.md](testing-and-robustness.md)).
- Later, live/FTMO trading must follow the same rule: the bot trades every signal; manual
  interventions are logged and measured against the system.
- Douglas's claim that a loss brings you "closer to a win" holds only if the edge is real and trades
  are independent; otherwise it is the gambler's fallacy.
