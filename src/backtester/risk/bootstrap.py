"""Stationary day-index bootstrap. Spec: risk-management.md > Monte Carlo report."""

import math

import numpy as np


def validate_block_days(block_days: float) -> None:
    if not math.isfinite(block_days) or block_days < 1:
        raise ValueError("block_days must be finite and >= 1")


def stationary_orders(
    n_days: int, runs: int, length: int, rng: np.random.Generator, block_days: float = 5
) -> np.ndarray:
    """Rows of circular blocks, with geometric lengths of mean `block_days`.

    Spec: risk-management.md > Monte Carlo report > A. Day sampling.
    Random restarts include the possibility of choosing the adjacent historic day.
    Vectorization tracks the most recent restart at every path position.
    """
    validate_block_days(block_days)
    if any(not isinstance(v, (int, np.integer)) or v < 0 for v in (n_days, runs, length)):
        raise ValueError("n_days, runs and length must be nonnegative integers")
    if length == 0:
        return np.empty((runs, 0), dtype=int)
    if n_days == 0:
        raise ValueError("cannot sample a nonempty path from zero days")
    starts = rng.integers(n_days, size=(runs, length))
    restart = rng.random((runs, length)) < 1 / block_days
    restart[:, 0] = True
    positions = np.arange(length)
    last = np.maximum.accumulate(np.where(restart, positions, 0), axis=1)
    return (np.take_along_axis(starts, last, axis=1) + positions - last) % n_days
