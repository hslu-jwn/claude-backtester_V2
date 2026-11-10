"""Energy report gates must pair matching disjoint report and control cells."""
from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace

from backtester.tools import timed_hold_gates as gates


def trade(day, value, symbol="USOIL"):
    at = datetime(2020, 1, 1, 15, tzinfo=UTC) + timedelta(days=day)
    return SimpleNamespace(symbol=symbol, entry_time=at, exit_time=at + timedelta(hours=1),
                           r_net=value, r_gross=value, spread_r=0., commission_r=0.,
                           swap_r=0., funding_r=0., conversion_r=0.)


def test_energy_matches_days_and_never_passes_unknown_integrity():
    settings = {"family": "F", "k": "0.15", "stop_atr": "1.0", "days": "report"}
    report = [trade(i * 14, 2) for i in range(20)] + [trade(i * 14, 1, "UKOIL") for i in range(20)]
    control = [trade(i * 14 + 1, -1) for i in range(20)]
    variants = {"r": {"settings": settings, "trades": report},
                "c": {"settings": {**settings, "days": "control"}, "trades": control}}
    result = gates.evaluate_energy(variants, date(2020, 1, 1), date(2020, 12, 31), None, None)
    assert result["r"]["baseline_difference"]["difference"] == 3
    assert not result["r"]["gates"]["no_data_integrity_failure"]
    assert not result["r"]["advances"]


def test_energy_overlapping_ny_dates_fail_closed():
    settings = {"family": "F", "k": "0.15", "stop_atr": "1.0", "days": "report"}
    variants = {"r": {"settings": settings, "trades": [trade(0, 2)]},
                "c": {"settings": {**settings, "days": "control"}, "trades": [trade(0, 1)]}}
    result = gates.evaluate_energy(variants, date(2020, 1, 1), date(2020, 12, 31), {}, {})
    assert result["r"]["baseline_difference"] is None
    assert not result["r"]["gates"]["effect_not_drift"]


def test_energy_cli_never_passes_skipped_integrity(tmp_path):
    import csv
    import json

    from test_timed_hold_gates import _write_variant

    _write_variant(tmp_path, "v1", {"USOIL": [1.0], "UKOIL": [1.0]})
    _write_variant(tmp_path, "v2", {"USOIL": [-1.0]}, offset=1)
    with (tmp_path / "variants.csv").open("w", newline="", encoding="utf8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["variant_id", "set.family", "set.k", "set.stop_atr", "set.days"])
        writer.writerows([["v1", "F", "0.15", "1.0", "report"],
                          ["v2", "F", "0.15", "1.0", "control"]])
    assert gates.main([str(tmp_path), "--mode", "energy_report", "--skip-integrity"]) == 0
    data = json.loads((tmp_path / "gates.json").read_text(encoding="utf8"))
    report = next(r for r in data["variants"].values() if r["settings"]["days"] == "report")
    assert not report["gates"]["no_data_integrity_failure"]
    assert data["settings"]["family_wise_level"] == 0.025


def test_energy_strategy_defects_fail_integrity_and_non_anchor_cannot_advance():
    settings = {"family": "F", "k": "0.30", "stop_atr": "1.0", "days": "report"}
    variants = {"r": {"settings": settings, "trades": [trade(0, 1)]},
                "c": {"settings": {**settings, "days": "control"}, "trades": [trade(1, 0)]}}
    failures = {"r": {"USOIL": [], "UKOIL": []}, "c": {}}
    records = {"r": [{"defects": ["missing_exit"]}], "c": []}
    row = gates.evaluate_energy(variants, date(2020, 1, 1), date(2020, 12, 31),
                                failures, records)["r"]
    assert not row["gates"]["no_data_integrity_failure"]
    assert row["anchor"] is False
    assert not row["advances"]


def test_energy_control_defects_fail_integrity():
    settings = {"family": "F", "k": "0.15", "stop_atr": "1.0", "days": "report"}
    variants = {"r": {"settings": settings, "trades": [trade(0, 1)]},
                "c": {"settings": {**settings, "days": "control"}, "trades": [trade(1, 0)]}}
    failures = {"r": {"USOIL": []}, "c": {"USOIL": [trade(1, 0)]}}
    records = {"r": [], "c": []}
    row = gates.evaluate_energy(variants, date(2020, 1, 1), date(2020, 12, 31), failures, records)["r"]
    assert not row["gates"]["no_data_integrity_failure"]
    failures["c"] = {"USOIL": []}
    records["c"] = [{"defects": ["missing_exit"]}]
    row = gates.evaluate_energy(variants, date(2020, 1, 1), date(2020, 12, 31), failures, records)["r"]
    assert not row["gates"]["no_data_integrity_failure"]
