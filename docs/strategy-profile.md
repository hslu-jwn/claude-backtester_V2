# Strategy condition profile

V2.6: descriptive analytics only; never changes trades, variant selection, DSR or trials.
Use adapter D1 candles (currently 17:00 America/New_York, DST-aware). A regime label uses
only candles closed at or before entry. Trend and volatility warm up independently;
any unknown component maps to the combined regime's single unknown row.

Each dimension partitions all trades: trend x volatility (six cells plus unknown), trend,
volatility, symbol, market class (shared classifier), entry session (sessions.py, latest
opened session, other outside sessions), direction, and UTC entry weekday.

Cells show count, effective count (daily holding-interval uniqueness within the cell),
raw win rate/net R/mean R, detrended net/mean R, one-sided IID BCa 90% lower mean bound
on detrended R (unavailable below ten trades), and raw exit-ordered peak-to-trough DD in R.
Detrending uses whole-period symbol drift, never cell-specific drift. Missing drift makes
the cell's detrended statistics and bound unavailable; trades remain counted.

Best is the highest detrended mean among cells with at least RegimeConfig.min_trades_best
(30) trades and a strictly positive lower bound. Otherwise report none with an explicit
reason. Strongest skill cells are the five cells across dimensions with positive bounds,
ranked by bound; these are descriptive, overlapping comparisons without multiplicity
or dependence correction. Equal scores retain dimension/cell order.

CLI: strategy_profile --strategy NAME (or --all, sequential strategies), optional symbols,
start/end, --set KEY=VALUE, --workers. Defaults match entry_screen's development period
and strategy symbols; test dates require --allow-test-period. Output profile.json and
profile.md under results/profiles/NAME_TIMESTAMP; one standard trial line per strategy,
family NAME-profile. Research adds profiles only for the chosen development variant and
test runs already executed, without rerunning strategies or adding trial lines.
