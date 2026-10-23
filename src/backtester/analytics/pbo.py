"""Spec: research-runner.md > Significance of the best variant. CSCV on MTM returns."""

from dataclasses import dataclass
from itertools import combinations

import numpy as np

from backtester.analytics.best_of_n import daily_matrix


@dataclass(frozen=True)
class PBOConfig:
    blocks: int = 16
    purge_days: int = 5

    def __post_init__(self):
        if (
            not isinstance(self.blocks, int)
            or isinstance(self.blocks, bool)
            or self.blocks < 2
            or self.blocks % 2
        ):
            raise ValueError("blocks must be an even integer >= 2")
        if (
            not isinstance(self.purge_days, int)
            or isinstance(self.purge_days, bool)
            or self.purge_days < 0
        ):
            raise ValueError("purge_days must be a nonnegative integer")


def _moments(block):
    # Shift before taking means: identical decimal values stay exactly constant.
    delta = block - block[0]
    mean_delta = delta.mean(0)
    return len(block), block[0] + mean_delta, np.square(delta - mean_delta).sum(0)


def _sharpe(moments, indices):
    count = sum(moments[i][0] for i in indices)
    reference = moments[indices[0]][1]
    mean = reference + sum(moments[i][0] * (moments[i][1] - reference) for i in indices) / count
    squares = sum(moments[i][2] + moments[i][0] * np.square(moments[i][1] - mean) for i in indices)
    variance = np.maximum(0, squares / (count - 1))
    sd = np.sqrt(variance)
    return np.divide(mean, sd, out=np.zeros_like(mean), where=sd > 0)


def cscv_pbo(values, config: PBOConfig | None = None) -> dict:
    """All half-block combinations; average OOS ranks and OOS-side boundary purge.

    Spec: research-runner.md > Significance of the best variant. Block sufficient
    statistics avoid rescanning all daily observations for every combination.
    """
    cfg = config or PBOConfig()
    matrix = daily_matrix(values)
    unavailable = {
        "pbo": None,
        "median_oos_rank": None,
        "degradation_slope": None,
        "pairs": [],
        "logits": [],
    }
    if matrix.shape[1] < 2:
        return {**unavailable, "reason": "requires at least two variants"}
    blocks = np.array_split(matrix, cfg.blocks)
    oos_blocks = [
        b[cfg.purge_days if i else 0 : len(b) - cfg.purge_days if i < cfg.blocks - 1 else len(b)]
        for i, b in enumerate(blocks)
    ]
    if min(map(len, oos_blocks)) < 2:
        return {**unavailable, "reason": "too few days: every purged block needs two observations"}
    full, purged = list(map(_moments, blocks)), list(map(_moments, oos_blocks))
    pairs, ranks = [], []
    for ins in combinations(range(cfg.blocks), cfg.blocks // 2):
        oos = [i for i in range(cfg.blocks) if i not in ins]
        is_scores, oos_scores = _sharpe(full, ins), _sharpe(purged, oos)
        winner = int(np.argmax(is_scores))
        chosen = oos_scores[winner]
        rank = (
            np.count_nonzero(oos_scores < chosen) + (np.count_nonzero(oos_scores == chosen) + 1) / 2
        )
        ranks.append(float(rank / (matrix.shape[1] + 1)))
        pairs.append([float(is_scores[winner]), float(chosen)])
    logits = np.log(np.array(ranks) / (1 - np.array(ranks)))
    x, y = np.array(pairs).T
    dx = x - x.mean()
    denominator = float(dx @ dx)
    slope = float(dx @ (y - y.mean()) / denominator) if denominator > 0 else None
    return {
        "pbo": float(np.mean(logits <= 0)),
        "median_oos_rank": float(np.median(ranks)),
        "degradation_slope": slope,
        "pairs": pairs,
        "logits": logits.tolist(),
        "blocks": cfg.blocks,
        "purge_days": cfg.purge_days,
        "reason": None,
    }
