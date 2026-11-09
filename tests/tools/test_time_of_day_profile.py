from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np
import pytest

from backtester.analytics.entry_screen import M1Data
from backtester.engine.costs import CostConfig
from backtester.tools import time_of_day_profile as tod


def candles(days, missing=()):
    zone = ZoneInfo("Europe/London")
    stamps, prices = [], []
    for day in days:
        day_offset = (day - days[0]).days
        for hour in range(25):
            local = datetime.combine(day, datetime.min.time(), zone) + timedelta(hours=hour)
            close = int(local.astimezone(UTC).timestamp())
            if (day, hour) not in missing:
                stamps.append(close - 60)
                prices.append(np.exp(0.0001 * (day_offset + (hour >= 9))))
    p = np.array(prices)
    return M1Data(np.array(stamps), p, p, p, p)


def test_hourly_returns_and_weekends():
    days = [date(2021, 1, 4) + timedelta(days=i) for i in range(7)]
    rows = tod.profile(candles(days), ZoneInfo("Europe/London"), days[0], days[-1], days[3])
    assert len(rows) == 24
    assert all(row["n"] == 5 for row in rows)
    assert rows[8]["mean_bp"] == pytest.approx(1)
    assert all(row["mean_bp"] == pytest.approx(0) for row in rows if row["hour"] != 8)
    assert rows[8]["n_first"] == 3
    assert rows[8]["n_second"] == 2


def test_dst_uses_local_clock():
    days = [date(2021, 1, 4), date(2021, 7, 5)]
    data = candles(days)
    assert int(datetime(2021, 1, 4, 8, tzinfo=UTC).timestamp()) in data.close_s
    assert int(datetime(2021, 7, 5, 7, tzinfo=UTC).timestamp()) in data.close_s
    rows = tod.profile(data, ZoneInfo("Europe/London"), days[0], days[-1], days[1])
    assert rows[8]["n"] == 2
    assert rows[8]["mean_bp"] == pytest.approx(1)


@pytest.mark.parametrize("hour", [8, 9])
def test_missing_endpoint_only_drops_affected_pairs(hour):
    days = [date(2021, 1, 4), date(2021, 1, 5)]
    rows = tod.profile(candles(days, {(days[0], hour)}), ZoneInfo("Europe/London"),
                       days[0], days[-1], days[1])
    assert rows[8]["n"] == 1
    assert rows[hour - 1]["n"] == 1
    assert rows[hour]["n"] == 1
    assert rows[10]["n"] == 2


def test_end_cutoff_and_default(monkeypatch, tmp_path):
    calls = []
    def load(symbol, sources, start, end):
        calls.append((start, end))
        return candles([date(2021, 1, 4)])
    monkeypatch.setattr(tod, "load_m1", load)
    with pytest.raises(SystemExit, match="2021-09-13"):
        tod.main(["EURUSD", "--zone", "Europe/London", "--end", "2021-09-14"])
    assert not calls
    tod.main(["EURUSD", "--zone", "Europe/London", "--out", str(tmp_path)])
    assert calls[0][1] == date(2021, 9, 13)
    assert (tmp_path / "EURUSD.csv").is_file()
    assert "Cost" in (tmp_path / "report.md").read_text(encoding="utf-8")


def test_cost_at_median_price():
    config = CostConfig()
    price = 1.2
    expected = (config.spread("EURUSD", price=price) +
                2 * config.slippage("EURUSD", price) +
                config.commission_price("EURUSD", price)) / price * 10000
    assert tod.cost_bp("EURUSD", price) == pytest.approx(expected)
