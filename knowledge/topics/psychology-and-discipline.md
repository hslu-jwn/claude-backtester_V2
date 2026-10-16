# Psychology and discipline

Sources: D = Douglas *Trading in the Zone*; H = Hougaard *Best Loser Wins*; K = Kaufman; RC = Carver; KD = Davey; WK = Kurt; EC = Chan.
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

## From Volman, Aziz and Coulling
- Volman: sit on the sidelines ~90 % of the time; take every *valid* setup and skip the rest without regret;
  a skipped trade stays skipped; review decisions after the session, not during; re-enter right after a
  stop-out if the setup re-forms; don't watch P/L in a trade.
- Aziz: a good day is a rule-following day; hide the P/L; stop when stressed; trade a written plan with
  if-then statements made before the open; simulator for 3 months first.
- Coulling: a signal means "get ready", not "enter"; patience.
- All three are discretionary and say so: Volman calls his edge "a personal perception", Coulling says
  her method cannot be automated, Aziz says mechanical systems lose. Coding their rules is our
  interpretation and must be tested, not assumed.


## From the method books (Carver, Davey, Kurt, Chan)
- **Meddling is the biggest cause of bad results** (RC ch.1): overriding the system, changing the risk target after losses, taking profits early.
  Commitment devices: objective rules, automation, a fixed vol target, starting small. Disposition effect: people take small profits and hold losers.
- Davey: decide beforehand when to start (after N months of incubation regardless of the equity curve), what to do with an open signal, and when to
  quit (max drawdown, losing streak, loss per week or month, win rate below X, equity-curve break); skipping or front-running signals invalidates the
  test; trade 3+ systems so none is micro-managed; after an operational error sync back with market orders; ~1 idea in 100-200 works (KD ch.21, 25).
- Kurt: a good hypothesis is falsifiable; a story that explains every outcome (profit or loss) gains from contradicting data, so write down the
  result that would make you drop the idea before the test (WK ch.18). Collecting trades that confirm the idea is the wrong direction (WK ch.1).
- Chan: steady mean-reversion profits breed over-leverage; do not override the model; start under-leveraged (EC p.61, 172).
- Steady wins with no losses usually mean negative skew not yet exposed (RC epilogue); a very high hit rate deserves suspicion, not comfort.
