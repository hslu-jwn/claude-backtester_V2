---
name: backtest-evaluation-research
description: "Use when researching online how to evaluate backtests, strategy performance, robustness, statistical significance, overfitting, or prop-firm pass probabilities. Produce a sourced research brief, not a trading-rule change."
---

# Backtest Evaluation Research

Research methods for evaluating historical strategy results and propose how to test them in this repository. Do not change or reinterpret strategy rules: `docs/` remains the source of truth, and any proposed rule change needs the user's decision.

## Research workflow

1. Read the relevant specifications, architecture, and current metrics before searching. Separate facts about this implementation from general research claims.
2. Define the question and scope: strategy and instruments, sample period, timeframe, data source, costs included, whether parameters were selected on the same history, and the decision the evaluation should inform. Call out unknowns.
3. Search the web with the available browsing/search tools. Prefer original papers, peer-reviewed publications, recognized academic publishers, official exchange/regulator documentation, and primary data-provider documentation. Use secondary articles to discover leads, not as sole support for material claims.
4. Verify each important claim against the source itself. Record authors, title, publication/date, a direct stable URL or DOI, what the source actually supports, and limitations. Distinguish published evidence, the source's assumptions, and your interpretation. Never invent citations or imply a gated source was read.
5. Compare multiple relevant sources where practical. Note disagreements, applicability limits, sample-size requirements, assumptions, and any fact that needs a current re-check.
6. Translate findings into a proposed evaluation plan, not an automatic code or strategy change. Ask the user before changing `docs/` rules or adopting a new performance objective.

If web research tools are unavailable, say so and request accessible source links; do not present unverified memory as current online research.

## Evaluate the backtest, not just its headline return

Check the design for:

- **Information leakage:** candle-close availability, higher-timeframe alignment, feature/label leakage, warm-up history, and use of future-confirmed patterns. Respect this project's strict no-lookahead invariant.
- **Data quality and selection:** missing or duplicated candles, feed/symbol history limits, instrument selection, survivorship or delisting effects where relevant, timezone/DST handling, and whether results depend on a narrow period.
- **Out-of-sample discipline:** separate discovery from evaluation; consider chronological holdouts or walk-forward evaluation. Do not shuffle individual time observations as if they were independent. Preserve the final holdout from repeated tuning.
- **Multiple testing and overfitting:** count the tried variants/parameter choices when known; research appropriate selection-bias methods (for example, probability of backtest overfitting or a deflated Sharpe ratio) and state their assumptions. A statistical correction does not repair bad data, leakage, or unrealistic fills.
- **Trading frictions and execution:** include spread, commissions, slippage, swap/financing, gaps, fill assumptions, and conservative intrabar ordering where applicable. Separate gross from net results and test plausible cost sensitivity.
- **Robustness and uncertainty:** examine trade count, time/regime and instrument breakdowns, parameter sensitivity, drawdown and recovery, and uncertainty estimates. Prefer resampling that respects dependence (for example, blocks or whole days when appropriate) over an unjustified IID trade shuffle.
- **Metric fit:** use several measures tied to the decision, such as net expectancy in R, drawdown, trade count, profit factor, and account-level outcomes. Explain what a metric omits; do not treat win rate, Sharpe, a Monte Carlo pass rate, or FTMO challenge outcome alone as proof of an edge.

## Repository-specific boundaries

- Strategy outputs are trades in R; money, costs, account constraints, and Monte Carlo belong to `risk/`, as specified in `docs/risk-management.md`.
- Existing Monte Carlo specifications may dictate their resampling unit. Research may recommend comparisons or sensitivity studies, but must not silently replace those rules.
- Backtest comparisons must disclose the history and data source used. Do not claim generalization beyond the tested instruments, period, feed, or execution assumptions.
- Do not use research to alter a strategy, tune a parameter, or change a performance target without the user's explicit direction and corresponding specification update.

## Deliverable

Return a concise research brief with:

1. The question, scope, and known limitations.
2. A short summary of findings, with direct citations next to claims.
3. A source table (source/date, relevant finding, caveat).
4. A practical evaluation design for this repository, including metrics, data split, costs, and robustness checks.
5. Open decisions or additional data needed. Clearly label recommendations as recommendations, not project rules.

Starter literature is listed in [references/starting-points.md](./references/starting-points.md); verify publication details and applicability during each research task.
