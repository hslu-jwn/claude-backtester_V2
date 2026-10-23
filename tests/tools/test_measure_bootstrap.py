"""Measurement table uses the real kind A output and explicitly names both samplings."""

from scripts import measure_bootstrap


def test_measurement_metrics_and_table():
    outputs = {}
    for sampling, dd in (("permutation", 4.0), ("block_bootstrap", 6.0)):
        outputs[sampling] = {
            "risks": {
                0.01: {
                    "stats": {"max_dd_pct": {"median": dd, "p95": dd + 2}, "p_dd_over_alert": 0.2},
                    "ftmo": {
                        "pass_probability": 0.6,
                        "attempts": 10,
                        "fail_daily": 1,
                        "fail_max": 3,
                        "unfinished_share": 0.1,
                    },
                }
            }
        }
    rows = measure_bootstrap.metrics("example", outputs)
    assert [r["sampling"] for r in rows] == ["permutation", "block_bootstrap"]
    assert all(r["breach_probability"] == 0.4 for r in rows)
    assert [r["dd_median_pct"] for r in rows] == [4.0, 6.0]
    report = "\n".join(measure_bootstrap.comparison_table(rows))
    for text in ("permutation", "block_bootstrap", "P(DD > alert)", "breach", "1%"):
        assert text in report
