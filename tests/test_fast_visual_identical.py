"""Fast and Visual execution parity. Spec: ROADMAP.md > V2.5.

Use the CLI's run_backtests + write_results entry and the app's real job starter,
without importing Dash. Only output location and a single worker are supplied to
the starter; loading, warm-up, strategy, engine and serialization remain real.
"""

from __future__ import annotations

import csv
import json
from datetime import date, timedelta
from functools import partial
from pathlib import Path

import pytest
from m1_frames import m1

from backtester.core.models import Timeframe
from backtester.data.cache import cache_path
from backtester.data.sources import SymbolSources
from backtester.run import run_backtests, write_results
from backtester.runner import TRADE_COLUMNS, RunSettings, start_run
from backtester.strategy.gap_fade.config import GapFadeConfig
from backtester.strategy.trend_following.config import TrendFollowingConfig
from backtester.ui import backtest_job

WARM_DAY = date(2026, 1, 5)
TRADE_DAY = WARM_DAY + timedelta(days=1)
SYMBOL = "XAUUSD"


def _cache_day(folder: Path, day: date, rows: list, mirror: bool) -> None:
    if mirror:
        rows = [(ts, 220 - o, 220 - lo, 220 - h, 220 - c) for ts, o, h, lo, c in rows]
    frame = m1(
        *((ts, float(o), float(h), float(lo), float(c), 1.0, 0.0) for ts, o, h, lo, c in rows),
        day=day.isoformat(),
    )
    path = cache_path(folder, SYMBOL, day)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(path, index=False)


@pytest.mark.parametrize("mirror", [False, True], ids=["original", "mirrored"])
@pytest.mark.parametrize("strategy", ["gap_fade", "trend_following"])
def test_fast_visual_identical(tmp_path, strategy, mirror):
    cache = tmp_path / "cache"
    if strategy == "gap_fade":
        config = GapFadeConfig(atr_period=1)
        # Previous NY cash session: range 100-110, close 105 => ATR 10.
        warm = [
            ("14:29", 105, 105, 105, 105),
            ("16:59", 105, 110, 100, 105),
            ("20:59", 105, 106, 104, 105),
        ]
        # Gap +3: short 108, stop 111, target 105; target hit next minute.
        active = [
            ("14:29", 108, 108, 108, 108),
            ("14:30", 108, 109, 104, 105),
            ("20:59", 105, 106, 104, 105),
        ]
        expected_exits = ["take_profit"]
    else:
        config = TrendFollowingConfig(timeframe=Timeframe.M15, breakout_period=3, atr_period=3)
        # Three flat 15m candles seed the breakout channel and ATR in warm-up.
        warm = [(ts, 110, 110.1, 109.9, 110) for ts in ("23:15", "23:30", "23:45")]
        # Breakout long, then reverse short without touching the long's 109.45 stop.
        # The short closes at end of data. Both trades have no target.
        active = [
            ("00:00", 110, 110.3, 109.95, 110.2),
            ("00:15", 110.2, 110.3, 110.1, 110.25),
            ("00:30", 110.2, 110.25, 109.6, 109.7),
            ("00:45", 109.7, 109.8, 109.6, 109.75),
        ]
        expected_exits = ["signal", "end_of_data"]

    _cache_day(cache, WARM_DAY, warm, mirror)
    _cache_day(cache, TRADE_DAY, active, mirror)
    sources = SymbolSources.single(cache, [SYMBOL])
    settings = RunSettings(strategy=config, warmup_days=1)
    preset = "Parity fixture"

    # This is the CLI execution entry explicitly allowed by V2.5's brief.
    result = run_backtests([SYMBOL], TRADE_DAY, TRADE_DAY, settings, sources, workers=1)
    fast = write_results(result, tmp_path / "fast", preset=preset)

    backtest_job.reset()
    job = None
    try:
        job = backtest_job.start(
            [SYMBOL],
            TRADE_DAY,
            TRADE_DAY,
            settings,
            sources,
            preset,
            starter=partial(start_run, out_dir=tmp_path / "visual", workers=1),
        )
        job.run.join(timeout=20)
        assert job.run.finished, "Visual backtest did not finish within 20 seconds"
        assert job.run.error is None, repr(job.run.error)
        assert not job.run.cancelled
        assert backtest_job.snapshot(job)["state"] == "done"
        visual = job.run.folder
        assert visual is not None

        with (fast / "trades.csv").open(newline="", encoding="utf-8") as stream:
            fast_rows = list(csv.reader(stream))
        with (visual / "trades.csv").open(newline="", encoding="utf-8") as stream:
            visual_rows = list(csv.reader(stream))
        assert fast_rows[0] == list(TRADE_COLUMNS)
        assert visual_rows == fast_rows  # Exact column order, row order and string values.
        assert len(fast_rows) == len(expected_exits) + 1  # Never pass on two empty lists.
        records = [dict(zip(fast_rows[0], row, strict=True)) for row in fast_rows[1:]]
        assert [row["exit_reason"] for row in records] == expected_exits
        assert all(bool(row["take_profit"]) == (strategy == "gap_fade") for row in records)
        assert all(row["entry_candle"].startswith(TRADE_DAY.isoformat()) for row in records)

        def read(folder, name):
            return json.loads((folder / name).read_text(encoding="utf-8"))

        assert read(fast, "settings.json") == read(visual, "settings.json")
        fast_summary = read(fast, "summary.json")
        visual_summary = read(visual, "summary.json")
        # Each invocation owns its folder and creation timestamp; compare everything else.
        for summary in (fast_summary, visual_summary):
            assert summary.pop("run_id")
            assert summary.pop("created")
        assert fast_summary == visual_summary
        assert fast_summary["combined"]["trades"] == len(expected_exits)
        assert fast_summary["days"][SYMBOL]["warmup_from"] == WARM_DAY.isoformat()
    finally:
        if job is not None and not job.run.finished:
            job.run.cancel()
            job.run.join()  # Never leave a background thread behind, even after a failure.
        backtest_job.reset()
