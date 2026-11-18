"""T-24 fat-tail power check. Spec: research-runner.md > Fat-tail power check (T-24).

Before a data look: simulate the card's planned sample (n periods, sd per period) under Gaussian, Student-t(3),
GARCH(1,1) volatility clustering and one-sided rare jumps (rare_loss: steady small gains and a rare large loss;
rare_gain: the mirror), all zero-mean and scaled to the same sd, and report how often the t gate passes at the card's
expected edge (power) and at zero edge (false pass). Same draws for both, so edge 0 gives power == false pass.
Symmetric fat tails barely move either number; rare_loss inflates false passes in short samples (the sample mean
is positive whenever the rare loss has not happened yet), which is the case the flag reports.
"""

from dataclasses import dataclass
from math import isfinite, sqrt

import numpy as np

SCENARIOS = ("gaussian", "student_t3", "garch", "rare_loss", "rare_gain")


@dataclass(frozen=True)
class PowerConfig:
    sims: int = 10_000
    seed: int = 42
    threshold: float = 3.0  # research-runner M4 / development gate
    two_sided: bool = False  # M9 two-sided cards: threshold 3.3, |t|
    floor: float = 0.15  # M4: pass chance below 15 % -> PARKED
    scenarios: tuple = SCENARIOS
    garch_alpha: float = 0.10
    garch_beta: float = 0.85
    burn_in: int = 200
    jump_prob: float = 0.03  # rare_loss / rare_gain: chance of the jump per period
    jump_size: float = 8.0  # jump in sd of the Gaussian part
    false_pass_ratio: float = 3.0  # flag when a scenario's false pass >= this x the Gaussian rate

    def __post_init__(self):
        if self.sims < 1 or self.burn_in < 0:
            raise ValueError("sims must be >= 1 and burn_in >= 0")
        if not set(self.scenarios) <= set(SCENARIOS) or not self.scenarios:
            raise ValueError(f"scenarios must be a non-empty subset of {SCENARIOS}")
        if self.garch_alpha < 0 or self.garch_beta < 0 or self.garch_alpha + self.garch_beta >= 1:
            raise ValueError("GARCH needs alpha, beta >= 0 and alpha + beta < 1")
        if not 0 < self.jump_prob < 1 or self.jump_size <= 0:
            raise ValueError("jump_prob must be in (0, 1) and jump_size > 0")


def draw(name, n, sd, cfg):
    """sims x n zero-mean P/L with standard deviation sd."""
    rng = np.random.default_rng([cfg.seed, SCENARIOS.index(name)])
    if name == "gaussian":
        return rng.standard_normal((cfg.sims, n)) * sd
    if name == "student_t3":
        return rng.standard_t(3, (cfg.sims, n)) * sd / sqrt(3)  # t(3) variance is 3
    if name in ("rare_loss", "rare_gain"):
        q, j = cfg.jump_prob, cfg.jump_size * (-1 if name == "rare_loss" else 1)
        x = rng.standard_normal((cfg.sims, n)) + j * (rng.random((cfg.sims, n)) < q) - j * q
        return x * sd / sqrt(1 + j * j * q * (1 - q))
    a, b = cfg.garch_alpha, cfg.garch_beta
    omega = sd**2 * (1 - a - b)
    var = np.full(cfg.sims, sd**2)
    out = np.empty((cfg.sims, n))
    z = rng.standard_normal((cfg.sims, n + cfg.burn_in))
    for i in range(n + cfg.burn_in):
        e = np.sqrt(var) * z[:, i]
        if i >= cfg.burn_in:
            out[:, i - cfg.burn_in] = e
        var = omega + a * e**2 + b * var
    return out


def _pass_rate(x, cfg):
    n = x.shape[1]
    t = x.mean(axis=1) / (x.std(axis=1, ddof=1) / sqrt(n))
    hit = np.abs(t) >= cfg.threshold if cfg.two_sided else t >= cfg.threshold
    return float(hit.mean())


def power_check(n, edge, sd, cfg=None):
    """Per scenario {power, false_pass}; min_power and verdict (PARK if any scenario is below cfg.floor)."""
    cfg = cfg or PowerConfig()
    if n < 3 or not (isfinite(edge) and isfinite(sd)) or sd <= 0:
        raise ValueError("need n >= 3, finite edge and sd > 0")
    out = {}
    for name in cfg.scenarios:
        x = draw(name, n, sd, cfg)
        out[name] = {"power": _pass_rate(x + edge, cfg), "false_pass": _pass_rate(x, cfg)}
    out["min_power"] = min(out[s]["power"] for s in cfg.scenarios)
    out["verdict"] = "PARK" if out["min_power"] < cfg.floor else "OK"
    base = out["gaussian"]["false_pass"] if "gaussian" in out else None
    out["false_pass_flags"] = [
        s
        for s in cfg.scenarios
        if base is not None
        and s != "gaussian"
        and out[s]["false_pass"] >= cfg.false_pass_ratio * max(base, 1 / cfg.sims)
    ]
    return out


def main(argv=None):
    import argparse

    p = argparse.ArgumentParser(description="T-24 fat-tail power check (before any data look)")
    p.add_argument("--n", type=int, required=True, help="planned periods (events, weeks, months)")
    p.add_argument(
        "--edge", type=float, required=True, help="expected net edge per period (halved published)"
    )
    p.add_argument("--sd", type=float, required=True, help="signal-free sd per period, same unit")
    p.add_argument("--two-sided", action="store_true", help="M9 card: |t| >= 3.3")
    p.add_argument("--sims", type=int, default=10_000)
    a = p.parse_args(argv)
    cfg = PowerConfig(sims=a.sims, two_sided=a.two_sided, threshold=3.3 if a.two_sided else 3.0)
    r = power_check(a.n, a.edge, a.sd, cfg)
    for s in cfg.scenarios:
        print(f"{s:11s} power {r[s]['power']:.3f}  false pass {r[s]['false_pass']:.4f}")
    print(
        f"min power {r['min_power']:.3f} -> {r['verdict']}; false-pass flags: {r['false_pass_flags'] or 'none'}"
    )


if __name__ == "__main__":
    main()
