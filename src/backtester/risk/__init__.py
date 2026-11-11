"""Risk management and prop-firm (FTMO) simulation. Spec: docs/risk-management.md.

Works on R trade lists only, so settings can be tested without re-running detection.
Modules: prop_rules, sizer, monte_carlo, adaptive, bootstrap, drawdown_bounds, prop_card
(the config / account_sim / sweep stubs were removed 2026-11-11, review C; the sweep is
`tools/risk_sweep.py`).
"""
