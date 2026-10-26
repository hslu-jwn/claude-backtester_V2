import json
from datetime import date

import pytest

from backtester.analytics.portfolio_search import Member, search
from backtester.tools import portfolio_candidates as pc


def saved_member(root):
    folder = root / "research" / "grid"
    run = folder / "variants" / "v1"
    run.mkdir(parents=True)
    info = {
        "strategy": "gap_fade",
        "symbols": ["US500"],
        "periods": {"development": {"start": "2020-01-01", "end": "2020-01-02"}},
        "chosen": {"id": "v1", "overrides": {}},
    }
    (folder / "research.json").write_text(json.dumps(info))
    (folder / "variants.csv").write_text("variant_id,flags\nv1,short\n")
    (run / "summary.json").write_text(json.dumps({"start": "2020-01-01", "end": "2020-01-02"}))
    (run / "settings.json").write_text("{}")
    (run / "daily.csv").write_text("date,net_r_exit_booked\n2020-01-01,1\n2020-01-02,-1\n")
    (run / "trades.csv").write_text("id,symbol\n")
    return run


def test_load_chosen_only_and_refuse_test_daily(tmp_path):
    run = saved_member(tmp_path)
    pool, errors = pc.load_members(tmp_path)
    assert not errors
    assert len(pool) == 1
    assert pool[0].id == "grid~v1"
    assert pool[0].values == (1, -1)
    (run / "daily.csv").write_text("date,net_r_exit_booked\n2021-09-14,99\n")
    pool, errors = pc.load_members(tmp_path)
    assert pool == [] and errors


def test_top_ten_queue_has_no_test_or_backtest(tmp_path):
    from backtester.jobs.queue import Queue

    pool = [Member(str(i), (date(2020, 1, 1),), (i,)) for i in range(5)]
    rows = search(pool)
    queue = Queue(tmp_path / "queue")
    ids = pc.queue_top(rows, pool, "net_r", queue, tmp_path)
    assert len(ids) == 10
    assert len(queue.jobs()) == 10
    for job in queue.jobs():
        assert job.argv[0:2] == ["backtester.tools.portfolio", "--existing"]
        assert "--test" not in job.argv and "--retest" not in job.argv
    assert pc.queue_top(rows, pool, "net_r", queue, tmp_path) == []


def test_test_reservation_refuses_same_set_and_failed_attempt(tmp_path):
    pc.reserve_test(["b", "a"], tmp_path)
    with pytest.raises(ValueError, match="already"):
        pc.reserve_test(["a", "b"], tmp_path)


def test_cli_can_select_set_outside_monte_carlo_top_ten(tmp_path, monkeypatch):
    from backtester.analytics.portfolio_search import set_id

    parts = [Member(i, (date(2020, 1, 1),), (1,), folder=i) for i in ("a", "b")]
    sid = set_id(["a", "b"])
    base = tmp_path / "portfolio"
    base.mkdir()
    (base / f"search_{pc.pool_hash(parts)}.json").write_text(
        json.dumps({"pool": ["a", "b"], "sets": [{"id": sid, "members": ["a", "b"]}]})
    )
    monkeypatch.setattr(pc, "load_members", lambda *a: (parts, []))
    path = pc.resolve_set(sid, tmp_path)
    assert json.loads(path.read_text())["id"] == sid


def test_parser_test_cli_only_needs_set_id():
    from backtester.tools.portfolio import parse_args

    args = parse_args(["--test", "abc"])
    assert args.test == "abc"


def test_cached_search_content_changes(tmp_path):
    a = Member("a", (date(2020, 1, 1),), (1,))
    b = Member("b", a.days, (2,))
    assert pc.pool_hash([a, b]) == pc.pool_hash([b, a])
    assert pc.pool_hash([a, b]) != pc.pool_hash([a, Member("b", a.days, (3,))])


def test_artifact_changes_invalidate_fingerprint(tmp_path):
    run = saved_member(tmp_path)
    before, _ = pc.load_members(tmp_path)
    (run / "trades.csv").write_text("id,symbol,extra\n")
    after, _ = pc.load_members(tmp_path)
    assert pc.pool_hash(before) != pc.pool_hash(after)


@pytest.mark.parametrize(
    "days,start",
    [
        ((date(2020, 1, 3), date(2020, 1, 6)), date(2020, 1, 3)),
        ((date(2020, 1, 6),), date(2020, 1, 4)),
    ],
)
def test_worker_reuses_lists_and_preserves_weekend_booking(tmp_path, monkeypatch, days, start):
    from datetime import UTC, datetime
    from types import SimpleNamespace

    from backtester.runner import RunSettings
    from backtester.settings import to_dict
    from backtester.tools import monte_carlo as mc
    from backtester.tools import portfolio

    settings = to_dict(RunSettings())
    settings["run"] = {"start": start.isoformat(), "end": days[-1].isoformat()}
    values = (0, 2) if len(days) == 2 else (2,)
    parts = [Member(i, days, values, settings=settings, folder=i) for i in ("a", "b")]
    at = datetime(2020, 1, 4, 12, tzinfo=UTC)  # Saturday -> Monday, never dropped
    trade = SimpleNamespace(entry_time=at, exit_time=at, r_net=2, r_gross=2, symbol="X")
    monkeypatch.setattr(pc, "read_trades", lambda _: [trade])
    monkeypatch.setattr(
        portfolio, "run_backtests", lambda *a, **k: pytest.fail("backtest forbidden")
    )
    monkeypatch.setattr(portfolio, "combined_fills", lambda *a, **k: None)
    monkeypatch.setattr(portfolio, "portfolio_block", lambda *a: {})
    received = []

    def summary(trades, *args, **kwargs):
        received.extend(trades)
        return {"meta": args[1]}

    monkeypatch.setattr(mc, "build_summary", summary)
    pc.existing_summary(parts, tmp_path, mc.ToolConfig(runs=2))
    assert sum(t.r_net for t in received) == 2
    assert [t.risk_weight for t in received] == [0.5, 0.5]


def test_one_time_test_fixed_mt5_and_trial_log(tmp_path, monkeypatch):
    from types import SimpleNamespace

    from backtester import runner
    from backtester.analytics.portfolio_search import set_id
    from backtester.analytics.trial_log import read_all
    from backtester.data.sources import SymbolSources
    from backtester.runner import RunSettings
    from backtester.settings import to_dict
    from backtester.tools import monte_carlo as mc

    parts = [
        Member(i, (date(2020, 1, 1),), (1,), symbols=("US500",), settings=to_dict(RunSettings()))
        for i in ("b", "a")
    ]
    sid = set_id(m.id for m in parts)
    monkeypatch.setattr(pc, "resolve_set", lambda *a: tmp_path / "members.json")
    monkeypatch.setattr(
        pc, "manifest_members", lambda *a: ({"members": [m.id for m in parts]}, parts)
    )
    monkeypatch.setattr(SymbolSources, "cached_days", lambda *a: [date(2021, 9, 14)])
    calls = []

    def run(symbols, start, end, settings, *, sources, workers):
        calls.append((start, end, sources, workers))
        return SimpleNamespace(trades=[])

    monkeypatch.setattr(runner, "run_backtests", run)
    monkeypatch.setattr(mc, "build_summary", lambda *a, **k: {})
    monkeypatch.setattr(mc, "render_report", lambda s: "report")
    pc.run_test(sid, tmp_path, mc.ToolConfig())
    assert len(calls) == 2
    assert all(c[0] == date(2021, 9, 14) and c[3] == 1 for c in calls)
    assert all(not c[2].preferred_dirs for c in calls)
    records = read_all(tmp_path / "trials.jsonl")
    assert len(records) == 1 and records[0].settings == {"member_ids": ["a", "b"]}
    with pytest.raises(ValueError, match="already"):
        pc.run_test(sid, tmp_path, mc.ToolConfig())
    assert len(calls) == 2


def test_combined_fills_uses_each_members_saved_costs(monkeypatch):
    from backtester.analytics.random_fills import RandomFillsResult
    from backtester.tools import portfolio

    seen = []

    def fills(trades, cfg, costs):
        seen.append((cfg.seed, costs))
        return RandomFillsResult(2, (1, 2), 1, 1.5, 2)

    monkeypatch.setattr(portfolio, "random_fills", fills)
    result = portfolio.combined_fills(
        [[], []], [0.5, 0.5], {}, 2, 42, component_costs=[{"X": "first"}, {"X": "second"}]
    )
    assert seen == [(42, {"X": "first"}), (43, {"X": "second"})]
    assert result.run_net_r == (1, 2)


def test_daily_regime_ignores_unfinished_day():
    from datetime import UTC, datetime, timedelta
    from types import SimpleNamespace

    from backtester.core.models import Candle

    days = (date(2020, 1, 25),)
    pool = [Member("a", days, (1,), symbols=("X",))]
    candles = [
        Candle(
            datetime(2020, 1, 1, tzinfo=UTC) + timedelta(days=i), 100 + i, 101 + i, 99 + i, 100 + i
        )
        for i in range(24)
    ]
    fetched = []

    def fetch(symbol, timeframe, start, end):
        fetched.append(end)
        return [c for c in candles if start <= c.ts < end]

    sources = SimpleNamespace(
        cached_days=lambda s: [c.ts.date() for c in candles],
        adapter=lambda s: SimpleNamespace(fetch=fetch),
    )
    before = pc.daily_regimes(pool, sources)
    # Jan 24 D1 is unfinished at Prague midnight starting Jan 25: its huge crash is unknowable.
    candles[-1] = Candle(candles[-1].ts, 123, 123, 1, 1)
    assert pc.daily_regimes(pool, sources) == before
    assert before["X"][days[0]].startswith("trend_up")
    assert all(d.date() < date(2021, 9, 14) for d in fetched)


def test_existing_summary_real_report_with_small_simulation(tmp_path, monkeypatch):
    from datetime import UTC, datetime, timedelta
    from types import SimpleNamespace

    from backtester.analytics.daily import weekdays
    from backtester.risk.drawdown_bounds import DrawdownBoundsConfig
    from backtester.runner import RunSettings
    from backtester.settings import to_dict
    from backtester.tools import monte_carlo as mc
    from backtester.tools import portfolio

    days = tuple(weekdays(date(2020, 1, 1), date(2020, 2, 28)))
    trades = []
    for i, day in enumerate(days):
        at = datetime.combine(day, datetime.min.time(), UTC) + timedelta(hours=12)
        r = 1 if i % 3 else -1
        trades.append(
            SimpleNamespace(
                symbol="US500",
                entry_time=at,
                exit_time=at + timedelta(hours=1),
                entry=100,
                initial_stop=99,
                exit_reason="signal",
                r_net=r,
                r_gross=r,
                spread_r=0,
                commission_r=0,
                swap_r=0,
                funding_r=0,
            )
        )
    parts = [
        Member(
            i,
            days,
            tuple(t.r_net for t in trades),
            folder=i,
            strategy="session_zone_sweep",
            symbols=("US500",),
            settings=to_dict(RunSettings()),
        )
        for i in ("a", "b")
    ]
    monkeypatch.setattr(pc, "read_trades", lambda _: trades)
    monkeypatch.setattr(portfolio, "run_backtests", lambda *a, **k: pytest.fail("no backtest"))
    config = mc.ToolConfig(
        runs=3, paths=0, bounds=DrawdownBoundsConfig(outer=2, inner=3, horizon_days=5)
    )
    summary = pc.existing_summary(parts, tmp_path, config, log=lambda _: None)
    assert summary["robustness"]["net_r"] == sum(t.r_net for t in trades)
    assert "Portfolio" in portfolio.render_report(summary)
    assert "class='banner'" not in portfolio.render_report(summary, include_verdict=False)
    assert summary["meta"]["source"] == "development"
