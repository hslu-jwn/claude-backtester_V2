"""How good a liquidity sweep was: what price did after the sweep existed.

Research measure for comparing sweep rules (tools/sweep_study.py), not a strategy. Entry is
the close of the BOS candle (a sweep exists from there, so nothing here needs the future
to *find* the sweep), the stop is the sweeping wick, the risk their distance. Over the
next `horizon` candles of the same timeframe:

- `r1` / `r2`: result in R of a 1R / 2R target with that stop (conservative: a candle that
  holds both the stop and the target counts as the stop; no target and no stop: the close
  of the last candle in R, limited to -1 .. target);
- `mfe_r`: furthest favorable move before the stop candle, in R;
- `stopped`: the stop was hit within the horizon;
- `fav` / `adv` / `drift`: furthest favorable move, furthest adverse move and the close of
  the last candle, in price, over the whole horizon (the stop ignored).

Gross: no spread or commission.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from backtester.core.models import Candle, Direction


@dataclass(frozen=True, slots=True)
class SweepOutcome:
    entry: float
    risk: float  # price distance entry -> sweeping wick
    mfe_r: float
    stopped: bool
    r1: float
    r2: float
    fav: float
    adv: float
    drift: float


def _target_result(
    candles: Sequence[Candle], start: int, stop: int, entry: float, risk: float,
    bearish: bool, target: float,
) -> float:  # fmt: skip
    for j in range(start, stop):
        c = candles[j]
        adverse = (c.high - entry) if bearish else (entry - c.low)
        favorable = (entry - c.low) if bearish else (c.high - entry)
        if adverse >= risk:
            return -1.0
        if favorable >= target * risk:
            return target
    last = candles[stop - 1].close
    move = (entry - last) if bearish else (last - entry)
    return max(-1.0, min(target, move / risk))


def sweep_outcome(
    candles: Sequence[Candle], direction: Direction, extreme: float, index: int, horizon: int
) -> SweepOutcome | None:
    """Outcome of a sweep whose BOS candle is `candles[index]` and whose wick is `extreme`;
    None without risk (the BOS closed at the wick) or without a later candle."""
    entry = candles[index].close
    bearish = direction is Direction.BEARISH
    risk = (extreme - entry) if bearish else (entry - extreme)
    start, stop = index + 1, min(len(candles), index + 1 + horizon)
    if risk <= 0 or start >= stop:
        return None
    mfe, stopped, fav, adv = 0.0, False, 0.0, 0.0
    for j in range(start, stop):
        c = candles[j]
        up, down = c.high - entry, entry - c.low
        adverse, favorable = (up, down) if bearish else (down, up)
        fav, adv = max(fav, favorable), max(adv, adverse)
        if not stopped and adverse >= risk:
            stopped = True
        if not stopped:
            mfe = max(mfe, favorable)
    last = candles[stop - 1].close
    return SweepOutcome(
        entry,
        risk,
        mfe / risk,
        stopped,
        _target_result(candles, start, stop, entry, risk, bearish, 1.0),
        _target_result(candles, start, stop, entry, risk, bearish, 2.0),
        fav,
        adv,
        (entry - last) if bearish else (last - entry),
    )
