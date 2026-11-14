"""Weekly funding carry research book (no engine strategy).

Spec: strategy-crypto_carry.md › Rule (frozen).
"""

from .book import CryptoCarryConfig, pick_legs, signal, week_result

__all__ = ["CryptoCarryConfig", "pick_legs", "signal", "week_result"]
