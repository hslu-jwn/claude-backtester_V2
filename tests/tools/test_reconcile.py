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


def test_no_history_probe_evidence_and_boundaries(tmp_path):
    live = tmp_path / "live"
    day = live / "2026-10-27"
    day.mkdir(parents=True)
    anchor = dict(paper(T + timedelta(minutes=30)), symbol="GBPUSD", ticket="42")
    fill = dict(paper(T + timedelta(minutes=45)), symbol="EURUSD", ticket="43")
    pd.DataFrame([anchor, fill]).to_csv(day / "paper.csv", index=False)
    (live / "probe_stdout_run3.log").write_text(
        "16:00:00 connected\n16:00:01 no_history symbol=EURUSD\n"
        "16:30:02 order symbol=GBPUSD ticket=42 confirmed=True\n",
        encoding="utf-16",
    )
    runs, skipped = rec.load_probe_history(live)
    assert not skipped
    assert runs[0].start == T
    assert runs[0].symbols == {"EURUSD"}
    papers, _ = rec.load_demo(live, T, None, "fp", None)
    engines = [
        engine(T + timedelta(minutes=15)),
        engine(T + timedelta(minutes=15), symbol="GBPUSD"),
        engine(T + timedelta(minutes=50)),
    ]
    rows = rec.reconcile(
        [], engines, papers + [paper(T), paper(T + timedelta(minutes=60))], set(), history=runs
    )
    assert [r["explanation"] for r in rows] == [
        "no price history at bot start",
        "unexplained",
        "unexplained",
    ]
    report = rec.build_report(rows, runs, skipped)
    assert "2026-10-27 16:00:00+00:00" in report and "EURUSD" in report


def test_probe_without_date_is_skipped_and_reported(tmp_path):
    (tmp_path / "probe_stdout.log").write_text(
        "16:00:00 connected\n16:00:01 no_history symbol=EURUSD\n", encoding="utf-8"
    )
    runs, skipped = rec.load_probe_history(tmp_path)
    assert runs == []
    assert skipped == ["probe_stdout.log"]
    assert "probe_stdout.log" in rec.build_report([], runs, skipped)


def test_probe_non_history_evaluation_and_existing_reason(tmp_path):
    day = tmp_path / "2026-10-27"
    day.mkdir()
    pd.DataFrame([dict(paper(T + timedelta(minutes=30)), ticket="42")]).to_csv(
        day / "paper.csv", index=False
    )
    (tmp_path / "probe_stdout.log").write_text(
        "16:00:00 connected\n16:00:01 no_history symbol=EURUSD\n"
        "16:10:00 skip symbol=EURUSD reason=other\n"
        "16:30:02 order symbol=EURUSD ticket=42 confirmed=True\n",
        encoding="utf-8",
    )
    runs, skipped = rec.load_probe_history(tmp_path)
    assert not skipped
    p = [paper(T), paper(T + timedelta(minutes=30))]
    first = engine(T + timedelta(minutes=5))
    later = engine(T + timedelta(minutes=15))
    rows = rec.reconcile([], [first, later], p, set(), history=runs)
    assert [r["explanation"] for r in rows] == ["no price history at bot start", "unexplained"]
    skipped_paper = [dict(paper(T + timedelta(minutes=5)), status="skipped", reason="risk")]
    assert (
        rec.reconcile([], [first], p, set(), skipped_paper, history=runs)[0]["explanation"]
        == "risk"
    )


def test_trade_record_ends_missing_history_without_paper_fill(tmp_path):
    day = tmp_path / "2026-10-27"
    day.mkdir()
    pd.DataFrame([dict(paper(T + timedelta(minutes=30)), symbol="GBPUSD", ticket="42")]).to_csv(
        day / "paper.csv", index=False
    )
    pd.DataFrame(
        [
            {
                "ticket": "43",
                "symbol": "EURUSD",
                "entry_time": (T + timedelta(minutes=10)).isoformat(),
            }
        ]
    ).to_csv(day / "trades.csv", index=False)
    (tmp_path / "probe_stdout.log").write_text(
        "16:00:00 connected\n16:00:01 no_history symbol=EURUSD\n"
        "16:30:02 order symbol=GBPUSD ticket=42 confirmed=True\n",
        encoding="utf-8",
    )
    runs, _ = rec.load_probe_history(tmp_path)
    rows = rec.reconcile(
        [],
        [engine(T + timedelta(minutes=15))],
        [paper(T), paper(T + timedelta(minutes=30))],
        set(),
        history=runs,
    )
    assert rows[0]["explanation"] == "unexplained"
