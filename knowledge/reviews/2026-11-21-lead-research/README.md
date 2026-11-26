# Lead research review — 2026-11-21

This folder is a research-only review of `backtester-claude_V2`. It maps what the project has already tested,
records the strongest new evidence found by three parallel research streams, and turns that evidence into a
small ranked queue. It does **not** authorize a strategy, consume a test set, or change the backtester, ledger,
ideas registry, data, or source code.

## Bottom line

The project has not overlooked a large collection of easy OHLC edges. It has already searched the familiar
intraday, session, gap, breakout, reversal, trend, calendar, lead-lag, and cross-asset families deeply. Most fail
after realistic costs or lack independent power. The immediate operational priority remains the existing
forward-validation shelf, especially Strategy 20 and I-109. Frozen share periods start 2026-11-18 and crypto
periods 2026-11-23; the scheduled logger first collects them on 2026-12-03.

Four research leads are sufficiently distinct and strong enough to preserve near the top, all behind a data gate:

1. **Post-earnings employee selling at high-stock-compensation firms:** the largest direct new return estimate, but
   only B− working-paper evidence—the result was omitted from the published AER article and has no independent
   replication. First audit point-in-time EDGAR coverage, timing, power, and borrow; require a frozen post-2020 test.
2. **SEC Rule 201 threshold discontinuity:** the SEC identifies the NYSE/Nasdaq daily trigger archives it used.
   Run only a signal-free retrieval/completeness, event-count, and power audit first; a minute-bar low is not proof
   of activation, and the paper is causal evidence rather than an executable next-bar strategy.
3. **CRSP fast-track IPO inclusion:** a large forced purchase after the fifth trading day, materially different
   from ordinary quarterly index reviews. Public replication of eligibility is the first blocker.
4. **Non-overnight follow-on-offering reversal:** a peer-reviewed US study reports a 2.5% pre-pricing decline that
   reverses within seven days. First reconstruct public post-2015 announcement/pricing timestamps and event breadth;
   the source sample ends in 2014 and contains no executable cost test.

Same-calendar-month stock seasonality remains the strongest historical anomaly found, but the current 2016+
share history is too short for a source-matched test. It is a data-acquisition candidate, not a live queue item.

The most urgent project correction is I-105: its frozen rule observes the official opening price and claims an
entry in that same opening auction, but the auction order must be submitted before the price exists. Official
auction prints remain mandatory for rules that can know their signal before the auction. End-of-day reversal,
dividend-month pressure, cash merger arbitrage, Schedule 13D drift, 52-week-high momentum, pairs, residual
reversal, BTP auction cycles, and short-horizon crypto effects are lower-priority, data-blocked, or overlay-only.
A new international rights-issue family also survives only as a return-blind feasibility audit: its open 2,583-event
dataset is useful, but the modeled median spread is negative, extreme outliers drive the mean, and the US/Alpaca
route is operationally uneconomic.

Two cheap implementation scouts also survive: pre-price a narrow Databento pull to validate I-109 rolls, spreads,
and 15:00 fills; and measure Strategy 20's actual overlap with Binance's promotional zero-maker USDC contracts.
Neither is new alpha, and the latter is a separate forward execution variant.

## Files

| File | Purpose |
|---|---|
| `00-project-map.md` | Current strategies, data, exhausted families, and binding gaps |
| `01-ranked-opportunities.md` | Ranked candidates with exact next decisions and test skeletons |
| `02-evidence-register.md` | Primary sources, samples, claims, costs, and contrary evidence |
| `03-negative-findings.md` | Ideas rejected or deferred and why |
| `FINAL-REPORT.md` | Lead-agent synthesis and recommended sequence |

## Evidence policy

- Prefer primary papers, regulators, official data, and opened full text.
- A published causal effect is not automatically an executable edge.
- Apply the project’s M1–M12 and T-21 rules before any build: costs, power, preregistration, causal graph,
  placebo/absence tests, untouched test data, and shrinkage.
- Do not reopen closed families by relabeling a nearby indicator.
