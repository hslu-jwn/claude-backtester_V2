"""Trial log: every tried variant, one JSON line each, in `results/trials.jsonl`.

Spec: risk-management.md > Trial log and deflated Sharpe (ROADMAP 12.10). Append-only; on reading,
the last line per key (family, strategy, settings, symbols, period, source) wins, so rerunning a
variant is not a new trial. A count-only line (no stats) counts `count` trials for N but has no
Sharpe, so it does not enter V; V comes from the daily Sharpes only (ROADMAP 12.13). Corrupt or blank lines are skipped with a warning.
"""

from __future__ import annotations

import json
import warnings
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field, fields, is_dataclass
from datetime import UTC, date, datetime
from pathlib import Path

from backtester.analytics.daily import daily_net_r
from backtester.analytics.deflated_sharpe import trade_stats
from backtester.paths import RESULTS_DIR

TRIALS_FILE = "trials.jsonl"
COUNT_ONLY = "count-only"  # source / period marker of back-filled count-only lines


def default_path() -> Path:
    return RESULTS_DIR / TRIALS_FILE


@dataclass(frozen=True, slots=True)
class TrialRecord:
    family: str
    strategy: str
    settings: dict
    symbols: list
    start: str  # ISO date
    end: str
    source: str
    written: str  # ISO UTC time
    trades: int | None = None
    net_r: float | None = None
    mean: float | None = None
    sd: float | None = None
    skew: float | None = None
    kurt: float | None = None
    sharpe: float | None = None
    # daily net R (Prague days, empty days 0; ROADMAP 12.13); None on lines written before
    days: int | None = None
    day_mean: float | None = None
    day_sd: float | None = None
    day_skew: float | None = None
    day_kurt: float | None = None
    day_sharpe: float | None = None
    count: int = 1  # trials this line stands for (back-fill lines may be more than 1)
    note: str = field(default="")

    @property
    def key(self) -> str:
        return json.dumps(
            [self.family, self.strategy, self.settings, self.symbols, self.start, self.end,
             self.source],
            sort_keys=True,
        )  # fmt: skip


def settings_dict(config) -> dict:
    """A settings dataclass (or dict) as plain JSON types."""
    raw = asdict(config) if is_dataclass(config) and not isinstance(config, type) else config
    return json.loads(json.dumps(raw, default=str))


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def make_record(
    family: str, strategy: str, settings, symbols: Sequence[str], start: date, end: date,
    source: str, trades: Sequence, note: str = "",
) -> TrialRecord:  # fmt: skip
    """One variant's line from its trades (`r_net`, tz-aware `exit_time`): per-trade and daily
    statistics (the daily ones over the weekdays start..end)."""
    r_net = [t.r_net for t in trades]
    s = trade_stats(r_net)
    d = trade_stats(daily_net_r(trades, start, end))
    return TrialRecord(
        family, strategy, settings_dict(settings), list(symbols), start.isoformat(),
        end.isoformat(), source, now_iso(), s.n, float(sum(r_net)), s.mean, s.sd, s.skew, s.kurt,
        s.sharpe, d.n, d.mean, d.sd, d.skew, d.kurt, d.sharpe, 1, note,
    )  # fmt: skip


def count_only(family: str, strategy: str, count: int, note: str = "") -> TrialRecord:
    """Back-fill line: `count` trials for N, no numbers. Distinct notes stay distinct lines."""
    if count < 1:
        raise ValueError("count must be >= 1")
    return TrialRecord(
        family, strategy, {"note": note}, [], COUNT_ONLY, COUNT_ONLY, COUNT_ONLY, now_iso(),
        count=count, note=note,
    )  # fmt: skip


def append(record: TrialRecord, path: Path | None = None) -> None:
    path = path or default_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(record), sort_keys=True) + "\n")


def read_all(path: Path | None = None) -> list[TrialRecord]:
    """All lines, deduplicated (last line per key wins); missing file = none."""
    path = path or default_path()
    if not path.exists():
        return []
    known = {f.name for f in fields(TrialRecord)}
    by_key: dict[str, TrialRecord] = {}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            data = json.loads(line)
            if not isinstance(data, dict):
                raise TypeError("trial record must be an object")
            record = TrialRecord(**{k: v for k, v in data.items() if k in known})
        except (ValueError, TypeError):
            warnings.warn(f"trials log {path}: skipped bad line {number}", stacklevel=2)
            continue
        by_key[record.key] = record
    return list(by_key.values())


def family_trials(family: str, path: Path | None = None) -> list[TrialRecord]:
    return [r for r in read_all(path) if r.family == family]


def family_summary(lines: Sequence[TrialRecord]) -> tuple[int, list[float]]:
    """(N = trial count including count-only lines, daily Sharpes of the lines that have one;
    lines without daily statistics count for N only)."""
    return sum(r.count for r in lines), [r.day_sharpe for r in lines if r.day_sharpe is not None]
