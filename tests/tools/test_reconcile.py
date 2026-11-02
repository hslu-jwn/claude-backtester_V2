from datetime import UTC, datetime, timedelta

import pandas as pd
import pytest
from conftest import build_candles

from backtester.core.models import Timeframe
from backtester.core.series import CandleSeries
from backtester.engine.backtest import run_backtest
from backtester.strategy.fill_probe.config import FillProbeConfig
from backtester.strategy.fill_probe.strategy import FillProbe
from backtester.tools import reconcile as rec

T = datetime(2026, 10, 27, 16, tzinfo=UTC)


def paper(t=T, **kw):
    return dict(
        time_utc=t.isoformat(),
        symbol="EURUSD",
        side="buy",
        status="filled",
        reason="",
        ticket="1",
        comment="fp",
        sl="1",
        real_fill="1.11",
        **kw,
    )


def engine(t=T, **kw):
    row = {
        "symbol": "EURUSD",
        "signal_time": t,
        "side": "buy",
        "sl": 1.0,
        "entry_fill": 1.1,
        "exit_time": t + timedelta(minutes=20),
        "exit_reason": "signal",
        "exit_price": 1.2,
        "r_gross": 1.0,
        "r_net": 0.8,
    }
    row.update(kw)
    return row


def demo(p, **kw):
    row = dict(
        p,
        signal_time=rec._parse_time(p["time_utc"]),
        entry_fill=1.11,
        exit_time=T + timedelta(minutes=20),
        exit_reason="signal",
        exit_price=1.2,
        r_gross=1.0,
        r_net=0.7,
    )
    row.update(kw)
    return row


def test_matching_and_explanations():
    p = paper()
    row = rec.reconcile([demo(p)], [engine()], [p], {("EURUSD", T)})[0]
    assert row["status"] == "matched"
    assert row["diff_entry"] == pytest.approx(0.01)
    assert row["explanation"] == ""
    row = rec.reconcile([demo(p, side="sell", entry_fill=1.09)], [engine(side="sell")], [p], set())[
        0
    ]
    assert row["diff_entry"] == pytest.approx(0.01)
    row = rec.reconcile([demo(p, exit_reason="stop_loss")], [engine()], [p], set())[0]
    assert row["explanation"] == "exit reason: demo stop_loss, engine signal"
    row = rec.reconcile([demo(p, sl=1.01)], [engine()], [p], set())[0]
    assert row["explanation"] == "different stop (ATR / bars differ)"
    # 2026-11-03 (Opus, night run): direction first; a stop counts as different only beyond
    # STOP_TOLERANCE_R of the demo's stop distance (broker rounding is not a difference)
    row = rec.reconcile([demo(p, side="sell")], [engine()], [p], set())[0]
    assert row["explanation"] == "direction: demo sell, engine buy"
    near = 1.0 + 0.11 * (rec.STOP_TOLERANCE_R / 2)  # stop distance 0.11, half the tolerance
    assert rec.reconcile([demo(p, sl=near)], [engine()], [p], set())[0]["explanation"] == ""
    skipped = dict(p, status="skipped", reason="risk")
    assert rec.reconcile([], [engine()], [skipped], set())[0]["explanation"] == "risk"
    assert rec.reconcile([demo(p)], [], [p], set())[0]["explanation"] == "bar missing in cache"


def test_running_window():
    rows = [paper(T), paper(T + timedelta(hours=2))]
    for when in (T + timedelta(hours=1), T + timedelta(hours=3)):
        assert rec.reconcile([], [engine(when)], rows, set())[0]["explanation"] == "bot not running"


def test_read_filter_and_empty(tmp_path, capsys):
    day = tmp_path / "live" / "2026-10-27"
    day.mkdir(parents=True)
    pd.DataFrame([paper(), dict(paper(), comment="orb"), paper(T - timedelta(minutes=1))]).to_csv(
        day / "paper.csv", index=False
    )
    pd.DataFrame(
        [
            {
                "ticket": "1",
                "entry_fill": "1.11",
                "exit_time": T.isoformat(),
                "exit_reason": "signal",
                "exit_price": "1.2",
                "r_gross": "1",
                "r_net": "0.9",
            }
        ]
    ).to_csv(day / "trades.csv", index=False)
    all_paper, demos = rec.load_demo(tmp_path / "live", T, None, "fp", None)
    assert len(all_paper) == 3 and len(demos) == 1
    out = tmp_path / "out"
    assert rec.main(["--live-dir", str(tmp_path / "missing"), "--out", str(out)]) == 1
    assert not out.exists()
    assert "no" in capsys.readouterr().out.lower()


def test_report_cap():
    rows = rec.reconcile(
        [],
        [engine(T + timedelta(minutes=i)) for i in range(51)],
        [paper(T), paper(T + timedelta(minutes=51))],
        set(),
    )
    report = rec.build_report(rows)
    assert "engine_only" in report and "51" in report
    assert "By symbol" in report and "1 more" in report
    assert "51 unexplained" in report
    assert report.count("unexplained |") == 50


def test_real_engine_signal_times():
    candles = build_candles([(1.1, 1.101, 1.099, 1.1)] * 300, Timeframe.M1, T)
    trades = run_backtest(
        FillProbe("EURUSD", FillProbeConfig()), [CandleSeries("EURUSD", Timeframe.M1, candles)]
    )
    assert trades
    assert all(t.entry_time.minute % 30 == 0 for t in trades)


def test_output_inside_live_is_rejected(tmp_path, capsys):
    live = tmp_path / "live"
    assert rec.main(["--live-dir", str(live), "--out", str(live / "report")]) == 1
    assert not live.exists()
    assert "live" in capsys.readouterr().out.lower()


def test_missing_trade_exit_is_left_empty(tmp_path):
    day = tmp_path / "2026-10-27"
    day.mkdir()
    pd.DataFrame([paper()]).to_csv(day / "paper.csv", index=False)
    _, demos = rec.load_demo(tmp_path, T, None, "fp", None)
    row = rec.reconcile(demos, [engine()], [paper()], set())[0]
    assert row["demo_exit_time"] is None
    assert row["diff_exit_seconds"] == ""
