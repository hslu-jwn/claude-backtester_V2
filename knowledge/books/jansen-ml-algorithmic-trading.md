# Stefan Jansen, *Machine Learning for Algorithmic Trading*, Second Edition (Packt, 2020)

Short: **MLAT**. Read 2026-11-18 by Codex; Tier 4 methods book.

The book covers the workflow from market and alternative data through feature engineering, model validation, portfolio construction, and strategy backtesting. It uses Python examples to examine predictive signals and trading simulations. Its strongest contribution for this project is the treatment of leakage, model selection, and realistic execution.

**Citation limitation:** The supplied text has chapter and section breaks but no identifiable printed page numbers in the passages inspected. I could not verify the requested `MLAT p.N` references, so the notes below cite chapter and section names instead. They should not be treated as page-verified book notes.

## Testable ideas

- **Japanese equity random-forest forecasts** (MLAT, ch. 11, “The strategy – backtest with Zipline”): Predict one-day returns; each day go long the 25 highest positive forecasts and short the 25 lowest negative forecasts, provided there are at least 15 candidates on each side. Close positions that leave the selected forecasts. The preceding signal analysis reports a **5.16 bp** mean one-day top-minus-bottom quintile spread for an ensemble of three models; the trading backtest uses ten models, so that spread is not the backtest’s realized return. The backtest reports **5.5% annualized out-of-sample** for 2018–19, with a stated commission but no slippage. The book gives no compulsory counterparty mechanism. Data: point-in-time Japanese equity OHLCV and a historical universe; a separate US-share replication would need equivalent US data. **NEW**, but not a mechanism-backed candidate.

## Method notes

- **Use point-in-time inputs.** Align fundamentals with their actual release and account for restatements and split adjustments; where availability timestamps are missing, use conservative reporting lags. (MLAT, ch. 8, “Look-ahead bias”)
- **Reconstruct the historical universe.** Include securities subsequently delisted, acquired, or bankrupted to avoid conditioning the test on survival. (MLAT, ch. 8, “Survivorship bias”)
- **Purge overlapping labels.** Training observations whose outcomes overlap validation predictions can leak information; the book also describes an embargo after test periods and combinatorial cross-validation. The latter is a diagnostic, not automatically a simulation of chronological deployment. (MLAT, ch. 6, “Purging, embargoing, and combinatorial CV”)
- **Roll training and validation forward.** Specify training length, prediction horizon, and validation length explicitly, keeping the training and subsequent validation periods separated by the forecast horizon. (MLAT, ch. 11, “Time-series cross-validation”)
- **Count the trials.** Selecting a winner from many variations on the same history inflates apparent performance. The book discusses the deflated Sharpe ratio as an adjustment for multiple testing, non-normal returns, and sample length. (MLAT, ch. 8, “Getting the statistics right” and “The minimum backtest length and the deflated SR”)
- **Sequence signal and execution honestly.** A signal calculated from a closing price cannot automatically be filled at that same close; model when the signal arrives and when the order can execute. (MLAT, ch. 8, “Timing of decisions”)
- **Model implementability.** Include commissions, spreads, slippage, liquidity, operating hours, and short availability; fast-decaying signals can incur especially high turnover costs. (MLAT, ch. 8, “Transaction costs” and “Trading rules and execution”)
- **Inspect the distribution, not just mean quantile returns.** Wide overlap in daily return distributions can coexist with an attractive average separation. Compare forward-return quantiles across relevant holding periods. (MLAT, ch. 4, “Predictive performance by factor quantiles”)
- **Measure ranking skill through time.** The book uses Spearman rank correlation between factor values and forward returns and plots IC through time and by year, revealing uneven historical performance. (MLAT, ch. 4, “The information coefficient”)
- **Examine factor turnover alongside predictive strength.** Changes in quantile membership indicate the trading required to maintain a factor portfolio. (MLAT, ch. 4, “Factor turnover”)
- **Preserve realistic extremes.** Investigate outliers before clipping them: some are data errors, but others are genuine market events that the strategy must survive. (MLAT, ch. 8, “Outlier control”)
- **Mark positions to market.** Track the path of portfolio value and risk, since an attractive final return can conceal unacceptable interim losses. (MLAT, ch. 8, “Mark-to-market performance”)
- **Treat a signal spread as preliminary evidence.** The book’s separate minute-data example reports a **0.5 bp per minute** decile spread before costs but omits a trading backtest; it cannot establish a realizable net edge. (MLAT, ch. 12, signal evaluation)

## Verdict

The Japanese equity ML example has a stated size and trading rule, but the book does not identify a counterparty compelled to trade, and its signal spread and strategy backtest use different ensembles. It therefore does **not** meet the requested mechanism-plus-size threshold for a new research card. The main value here is the methods checklist, especially point-in-time data, leakage control, trial accounting, and execution timing.

