"""TS thresholds must not change the pre-existing E8/CAP gates."""
from datetime import date

from test_energy_report_gates import trade

from backtester.tools import timed_hold_gates as gates

POOL = ("EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "XAUUSD", "US500", "NAS100")


def evaluate(normal, stressed=None, integrity=True, covered=POOL):
    return gates.evaluate_daily_reversal(normal, normal if stressed is None else stressed,
        date(2020, 1, 1), date(2020, 12, 31), integrity, covered, setup="TS")


def test_ts_seven_symbol_pool_minimum_150_and_five_positive():
    trades = [trade(d, 1, s) for s in POOL for d in range(0, 360, 14)]
    row = evaluate(trades)
    assert set(row["symbols"]) == set(POOL)
    assert row["advances"]
    assert not evaluate(trades[:149])["gates"]["min_trades"]
    for positive, expected in [(4, False), (5, True)]:
        mixed = [trade(d, 1 if s in POOL[:positive] else -0.01, s)
                 for s in POOL for d in range(0, 360, 14)]
        assert evaluate(mixed)["gates"]["breadth"] is expected
    assert not evaluate(trades, covered=POOL[:-1])["gates"]["integrity"]
    assert not evaluate(trades, integrity=None)["advances"]
    assert not evaluate(trades, [trade(1, -1, "EURUSD")])["gates"]["positive_normal_and_doubled"]


def test_ts_cli_routes_settings_and_fails_unknown_calendar_audit(tmp_path, monkeypatch):
    import json
    from types import SimpleNamespace

    from backtester import settings
    from backtester.tools import research

    folder = tmp_path / "variants" / "v1"
    folder.mkdir(parents=True)
    (folder / "settings.json").write_text("{}")
    (folder / "sessions.json").write_text(json.dumps({s: [] for s in POOL}))
    normal = [trade(d, 1, s) for s in POOL for d in range(0, 360, 14)]
    doubled = [trade(d, 0.5, s) for s in POOL for d in range(0, 360, 14)]
    monkeypatch.setattr(settings, "from_dict", lambda raw: SimpleNamespace(
        strategy=SimpleNamespace(setup="TS"),
        engine=SimpleNamespace(costs="normal")))
    monkeypatch.setattr(gates, "daily_doubled_costs", lambda costs: "doubled")

    def replacing(obj, **kwargs):
        return SimpleNamespace(**{**vars(obj), **kwargs})

    monkeypatch.setattr(gates, "replace", replacing)
    monkeypatch.setattr(gates, "read_trades", lambda path: normal)
    monkeypatch.setattr(gates, "load_m1", lambda *args: object())
    monkeypatch.setattr(gates, "daily_integrity_failures", lambda *args: [])
    monkeypatch.setattr(gates.SymbolSources, "cached_days", lambda *args: [])

    def rerun(symbols, start, end, configured, sources, workers):
        assert configured.engine.costs == "doubled"
        assert tuple(symbols) == POOL and workers == 1
        return SimpleNamespace(trades=doubled, runs={s: SimpleNamespace(sessions=[]) for s in POOL})

    monkeypatch.setattr(research, "run_period", rerun)
    output = gates.daily_cli(tmp_path, [{"variant_id": "v1", "set.ts_lookback": 20}],
        date(2020, 1, 1), date(2020, 12, 31), {"cache_dirs": {}, "symbols": list(POOL)}, False)
    row = next(iter(output["variants"].values()))
    assert set(row["symbols"]) == set(POOL)
    assert row["gates"]["min_trades"] and row["gates"]["breadth"]
    assert not row["gates"]["integrity"] and not row["advances"]
    assert row["integrity_details"]["exchange_calendar_audited"] is False
    assert row["doubled"]["net_r"]["normal"] == len(doubled) * 0.5
