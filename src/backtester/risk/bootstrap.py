"""Compatibility API for the shared stationary sampler; unchanged sampling behavior.

Spec: risk-management.md > Monte Carlo report.
"""

from backtester.analytics.bootstrap import stationary_orders, validate_block_days

__all__ = ["stationary_orders", "validate_block_days"]
