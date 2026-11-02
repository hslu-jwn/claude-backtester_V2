# ruff: noqa: F811
import csv

from backtester.analytics.records import read_trades
from backtester.analytics.robustness import load_slippage_p90, stressed_net, stressed_net_p90
from backtester.engine.costs import CostConfig
from backtester.settings import from_dict
from tests.tools.test_intake import payload  # noqa: F401
from tests.tools.test_intake_envelopes import claimed, emit, folder, read, umbrella, validate, write  # noqa: F401


def declared(folder, ids=("v002", "v001")):
    (folder / "variants.csv").write_text(
        "variant_id,rank\n" + "".join(f"{i},1\n" for i in ids), encoding="utf-8"
    )


def trades(folder):
    folder.mkdir(parents=True, exist_ok=True)
    rows = [(-1, -1.1, "stop_loss"), (2, 1.8, "take_profit"), (1, 0.9, "take_profit")]
    fields = [
        "id",
        "symbol",
        "direction",
        "entry_time",
        "entry_candle",
        "entry",
        "initial_stop",
        "exit_time",
        "exit_price",
        "exit_reason",
        "r_gross",
        "r_net",
    ]
    with (folder / "trades.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for i, (gross, net, reason) in enumerate(rows):
            writer.writerow(
                {
                    "id": i,
                    "symbol": "NAS100",
                    "direction": "long",
                    "entry_time": "2020-01-01T00:00:00+00:00",
                    "entry_candle": "2020-01-01T00:00:00+00:00",
                    "entry": 100,
                    "initial_stop": 90,
                    "exit_time": "2020-01-01T01:00:00+00:00",
                    "exit_price": 100,
                    "exit_reason": reason,
                    "r_gross": gross,
                    "r_net": net,
                }
            )


def setup_cells(folder):
    declared(folder)
    for ident in ("v001", "v002"):
        run = folder / "variants" / ident
        trades(run)
        write(
            run / "scorecard.json",
            {
                "overrides": {"n": ident},
                "scorecard": {"half_first_net_r": 1.23456789, "half_second_net_r": 0.4},
            },
        )
    write(
        folder / "variants/v001/settings.json",
        {
            "run": {"symbols": ["NAS100"]},
            "strategy": {"range_minutes": 5},
            "engine": {"costs": {"slippage_enabled": False}},
        },
    )


def test_manifest_values_and_costs(tmp_path):
    from backtester.tools.intake_cells import cell_manifest

    setup_cells(tmp_path)
    rows = cell_manifest(tmp_path)
    assert [r["cell_id"] for r in rows] == ["v001", "v002"]
    for row in rows:
        assert row["parameters"] == {"n": row["cell_id"]}
        assert row["status"] == "COMPLETED"
        assert row["trades"] == 3
        assert row["gross_total_r"] == 2 and row["net_total_r"] == 1.6
        assert row["gross_mean_r"] == 0.666667 and row["net_mean_r"] == 0.533333
        assert row["stop_rate"] == 0.333333
        assert row["half_first_net_r"] == 1.234568 and row["half_second_net_r"] == 0.4
        ts = read_trades(tmp_path / "variants" / row["cell_id"])
        costs = (
            from_dict(read(tmp_path / "variants/v001/settings.json")).engine.costs
            if row["cell_id"] == "v001"
            else CostConfig()
        )
        assert row["cost_stresses"] == {
            "factor_1.5": round(stressed_net(ts, 1.5), 6),
            "factor_2.0": round(stressed_net(ts, 2), 6),
            "fill_p90": round(stressed_net_p90(ts, load_slippage_p90(), costs), 6),
        }
    assert "default" in str(rows[1]["notes"]).lower()


def test_missing_or_unreadable_cell(tmp_path):
    from backtester.tools.intake_cells import cell_manifest

    setup_cells(tmp_path)
    (tmp_path / "variants/v002/trades.csv").unlink()
    rows = cell_manifest(tmp_path)
    assert rows[0]["status"] == "COMPLETED"
    assert rows[1]["status"] == "FAILED" and rows[1]["reason"]
    assert all(
        rows[1][k] is None
        for k in (
            "trades",
            "gross_mean_r",
            "net_mean_r",
            "gross_total_r",
            "net_total_r",
            "stop_rate",
            "half_first_net_r",
            "half_second_net_r",
            "cost_stresses",
        )
    )
    import shutil

    shutil.rmtree(tmp_path / "variants/v002")
    assert cell_manifest(tmp_path)[1]["status"] == "FAILED"


def test_accounting(tmp_path):
    from backtester.tools.intake_cells import trial_accounting

    declared(tmp_path)
    for i in range(3):
        (tmp_path / "sensitivity" / str(i)).mkdir(parents=True)
    assert trial_accounting(tmp_path, {}, 5) == {
        "declared_cells": 2,
        "sensitivity_runs": 3,
        "trial_log_count": 5,
    }


def test_envelope_declared_cells_and_fallback(umbrella, claimed, folder):
    from backtester.analytics.trial_log import TrialRecord, append

    setup_cells(folder)
    info = read(folder / "research.json")
    info["sensitivity"] = {"some_result": 1}
    write(folder / "research.json", info)
    append(
        TrialRecord(
            "other",
            "opening_range",
            {},
            ["NAS100"],
            "2020-01-02",
            "2020-01-03",
            "research",
            "fixed",
            count=4,
            series="research/tiny/variants/v001/daily.csv",
        ),
        umbrella / "results/trials.jsonl",
    )
    out = emit(umbrella, claimed, folder)
    validate(umbrella, out, "result")
    data = read(out)
    assert data["variants_tried"] == 2
    assert len(data["robustness"]["cell_manifest"]) == 2
    assert data["robustness"]["trial_accounting"] == {
        "declared_cells": 2,
        "sensitivity_runs": 0,
        "trial_log_count": 5,
    }
    assert data["robustness"]["sensitivity"]["selectable"] is False


def test_no_variants_csv_falls_back(umbrella, claimed, folder):
    out = emit(umbrella, claimed, folder)
    data = read(out)
    assert data["variants_tried"] == 1
    assert data["robustness"]["trial_accounting"]["declared_cells"] is None


def test_redacted_robustness(umbrella, claimed, folder):
    info = read(folder / "research.json")
    run = umbrella / "results/holdout"
    for name in ("info.json", "summary.json", "settings.json"):
        write(run / name, read(folder / "variants/v001" / name))
    meta = read(run / "info.json")
    meta["submission"]["experiment_id"] = claimed.path.stem + "__FINAL_HOLDOUT__1"
    write(run / "info.json", meta)
    info["test"] = {"run_folder": "holdout"}
    write(folder / "research.json", info)
    write(
        umbrella / "results/intake" / claimed.path.stem / "test_authorization.json",
        {
            "authorized_by": "user",
            "quote": "Run the one-time test.",
            "authorized_at": "2026-10-28T12:00:00Z",
            "experiment_id": info["submission"]["experiment_id"],
        },
    )
    out = emit(umbrella, claimed, folder, stage="FINAL_HOLDOUT", holdout_disclosure="REDACTED")
    validate(umbrella, out, "result")
    assert read(out)["robustness"] == {}


def test_unreadable_trade_file_is_failed(tmp_path):
    from backtester.tools.intake_cells import cell_manifest

    setup_cells(tmp_path)
    (tmp_path / "variants/v002/trades.csv").write_text("not,a,trade\n", encoding="utf-8")
    rows = cell_manifest(tmp_path)
    assert rows[0]["status"] == "COMPLETED"
    assert rows[1]["status"] == "FAILED" and rows[1]["reason"]
