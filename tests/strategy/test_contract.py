"""Contract tests every registered strategy gets for free (ROADMAP research-speed plan, step 3).

The tests are parametrized over `strategy.registry.REGISTRY`: add a strategy to the registry and
it is checked here without a line of test code (see `strategy/_template/README.md`). Each strategy
runs on seeded synthetic M1 candles (`FIXTURES`, a trending random walk) resampled to the
timeframes it declares, through the real engine (`engine.run_backtest`).

Contracts (CLAUDE.md "Invariant #1", "Other design rules"):
1. Config: builds with defaults, frozen, JSON round trip through the settings the runner writes.
2. No lookahead: a run on a prefix gives the same entries as the same run on the longer series,
   a trade enters at the close of its candle, and a limit order is not decided from the candle it
   is filled in.
3. Deterministic: two runs give identical trades; variants are independent of run order.
4. R only: trades carry R values, no money or lot fields; stop distance > 0; exit reason set.
5. Sweepable: every config field is a name the research grid accepts.
6. Bullish / bearish mirror: NOT tested generically (see `test_mirror_is_not_generic`).

A strategy that makes no trade on its fixture is reported (`test_fixture_produces_trades`, xfail
with the strategy named) and the properties that need trades are skipped for it with a clear
reason; give it a better entry in `FIXTURES` (or a config in `extra_configs`).
"""

from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass, field, fields
from datetime import UTC, datetime, timedelta
from functools import cache

import numpy as np
import pandas as pd
import pytest

from backtester.core.models import Timeframe
from backtester.core.series import CandleSeries
from backtester.data.resample import resample
from backtester.engine.backtest import Backtest, run_backtest
from backtester.engine.trade import TradeResult
from backtester.runner import RunSettings, candles_from_frame, jsonable
from backtester.settings import HIDDEN, from_json, to_json
from backtester.strategy.registry import REGISTRY, default_config, make_strategy
from backtester.tools.research_grid import valid_names

START = datetime(2026, 1, 5, tzinfo=UTC)  # a Monday in winter: no daylight-saving shift anywhere


@dataclass(frozen=True)
class Fixture:
    symbol: str
    price: float
    sigma: float  # st.dev of the M1 log return
    hours: tuple[int, int]  # UTC hours with candles each weekday: [from, to)
    days: int = 12  # weekdays
    drift_sigma: float = 0.0  # st.dev of the trend (per-minute log drift) redrawn every regime
    regime_minutes: int = 240
    seed: int = 1
    # configs run next to the default one (label -> config), e.g. the other entry modes
    extra_configs: dict = field(default_factory=dict)


def _no_wick_extra() -> dict:
    from backtester.strategy.no_wick.config import EntryMode, NoWickConfig

    # the default (wick share 0) rarely fires on random candles: allow small wicks, and cover the
    # limit-order entry modes
    return {
        f"wick05_{mode.value}": NoWickConfig(max_wick_share=0.05, entry_mode=mode)
        for mode in EntryMode
    }


FIXTURES: dict[str, Fixture] = {
    "session_zone_sweep": Fixture("XAUUSD", 2000.0, 0.0006, (0, 24), days=10, drift_sigma=2e-5),
    "ny_index_sweep": Fixture("NAS100", 18000.0, 0.0006, (12, 22), days=8, drift_sigma=2e-5),
    "no_wick": Fixture(
        "XAUUSD", 2000.0, 0.0006, (0, 24), days=6, drift_sigma=2e-5,
        extra_configs=_no_wick_extra(),
    ),
    "trend_following": Fixture("XAUUSD", 2000.0, 0.0006, (0, 24), days=40, drift_sigma=2e-5),
    "gap_fade": Fixture("US500", 5000.0, 0.0006, (13, 22), days=24, drift_sigma=2e-5),
    "opening_range": Fixture("US500", 5000.0, 0.0006, (13, 22), days=24, drift_sigma=2e-5),
}  # fmt: skip

# a registered strategy without an entry gets this generic one (its trades are then reported)
GENERIC = Fixture("XAUUSD", 2000.0, 0.0006, (0, 24), days=10, drift_sigma=2e-5)


def fixture_for(name: str) -> Fixture:
    return FIXTURES.get(name, GENERIC)


# --- synthetic candles ------------------------------------------------------------------------


def m1_frame(fx: Fixture) -> pd.DataFrame:
    """Seeded M1 candles (cache layout) of `fx.days` weekdays; open = previous close inside a
    session, a jump across the nightly break."""
    rng = np.random.default_rng(fx.seed)
    stamps = []
    day = START
    while len(stamps) < fx.days:
        if day.weekday() < 5:
            first = day + timedelta(hours=fx.hours[0])
            minutes = (fx.hours[1] - fx.hours[0]) * 60
            stamps.append(pd.date_range(first, periods=minutes, freq="min", tz="UTC"))
        day += timedelta(days=1)
    ts = stamps[0].append(stamps[1:])
    n = len(ts)
    regimes = rng.normal(0.0, fx.drift_sigma, n // fx.regime_minutes + 1)
    drift = np.repeat(regimes, fx.regime_minutes)[:n]
    returns = drift + rng.normal(0.0, fx.sigma, n)
    close = fx.price * np.exp(np.cumsum(returns))
    open_ = np.concatenate([[fx.price], close[:-1]])
    wick = np.abs(rng.normal(0.0, fx.sigma * 0.5, (2, n))) * close
    high = np.maximum(open_, close) + wick[0]
    low = np.minimum(open_, close) - wick[1]
    digits = 2
    frame = pd.DataFrame(
        {
            "ts": ts,
            "bid_open": open_, "bid_high": high, "bid_low": low, "bid_close": close,
            "bid_volume": rng.integers(50, 150, n).astype(float),
            "ask_open": open_, "ask_high": high, "ask_low": low,
            "ask_close": close + 0.0001 * fx.price * 0.01,
            "ask_volume": np.nan,
        }
    )  # fmt: skip
    price_cols = [c for c in frame.columns if c.startswith(("bid_", "ask_")) and "volume" not in c]
    frame[price_cols] = frame[price_cols].round(digits)
    # rounding must keep each candle consistent
    frame["bid_high"] = frame[["bid_high", "bid_open", "bid_close"]].max(axis=1)
    frame["bid_low"] = frame[["bid_low", "bid_open", "bid_close"]].min(axis=1)
    return frame


@cache
def series_for(name: str) -> tuple[CandleSeries, ...]:
    fx = fixture_for(name)
    strategy = make_strategy(fx.symbol, default_config(name))
    m1 = m1_frame(fx)
    out = []
    for tf in dict.fromkeys(strategy.timeframes):
        frame = resample(m1, tf, h4=strategy.h4_alignment)
        out.append(CandleSeries(fx.symbol, tf, candles_from_frame(frame)))
    return tuple(out)


def configs_for(name: str) -> dict[str, object]:
    return {"default": default_config(name), **fixture_for(name).extra_configs}


CASES = [
    pytest.param(name, label, id=f"{name}-{label}")
    for name in REGISTRY
    for label in configs_for(name)
]


def _strategy(name: str, config):
    return make_strategy(fixture_for(name).symbol, config)


def run(name: str, config, series=None) -> list[TradeResult]:
    return run_backtest(_strategy(name, config), series or series_for(name))


@cache
def trades_of(name: str, label: str) -> tuple[TradeResult, ...]:
    return tuple(run(name, configs_for(name)[label]))


def _need_trades(name: str, label: str) -> tuple[TradeResult, ...]:
    trades = trades_of(name, label)
    if not trades:
        pytest.skip(f"{name}/{label}: no trade on the fixture (see test_fixture_produces_trades)")
    return trades


# --- 0. the fixture itself --------------------------------------------------------------------


@pytest.mark.parametrize(("name", "label"), CASES)
def test_fixture_produces_trades(name, label):
    """Not a rule of the strategy: tells which strategies need a better fixture (FIXTURES)."""
    if not trades_of(name, label):
        pytest.xfail(
            f"{name}/{label}: no trade on the synthetic fixture, so the contracts that need trades"
            " are skipped for it; give it a better entry in FIXTURES"
        )
    assert len(trades_of(name, label)) >= 1


# --- 1. config --------------------------------------------------------------------------------


@pytest.mark.parametrize("name", list(REGISTRY))
def test_default_config_is_frozen_and_complete(name):
    config = default_config(name)
    assert type(config) is REGISTRY[name].config_cls
    assert dataclasses.is_dataclass(config)
    assert type(config).__dataclass_params__.frozen
    for f in fields(config):
        has_default = (
            f.default is not dataclasses.MISSING or f.default_factory is not dataclasses.MISSING
        )
        assert has_default, f"{name}: config field {f.name} has no default"
    first_field = fields(config)[0].name if fields(config) else None
    if first_field:
        with pytest.raises(dataclasses.FrozenInstanceError):
            setattr(config, first_field, getattr(config, first_field))
    _strategy(name, config)  # builds a strategy


@pytest.mark.parametrize(("name", "label"), CASES)
def test_config_round_trips_through_the_settings_json(name, label):
    config = configs_for(name)[label]
    settings = RunSettings(strategy=config)
    text = to_json(settings)
    json.loads(text)  # plain JSON
    back = from_json(text)
    assert back.strategy == config
    assert type(back.strategy) is REGISTRY[name].config_cls
    assert to_json(back) == text
    assert json.dumps(jsonable(config))  # the runner's own writer accepts it


# --- 2. no lookahead --------------------------------------------------------------------------


def _prefix(series: tuple[CandleSeries, ...], cut: datetime) -> tuple[CandleSeries, ...]:
    """Every series cut to the candles closed by `cut` (what exists at that time)."""
    out = []
    for s in series:
        view = s.view(len(s) - 1)
        kept = [c for c in view.last(len(s)) if c.ts + s.timeframe.duration <= cut]
        out.append(CandleSeries(s.symbol, s.timeframe, kept))
    return tuple(out)


ENTRY_FIELDS = (
    "symbol", "direction", "entry_time", "entry_candle", "entry", "entry_fill",
    "initial_stop", "take_profit", "take_profit_2", "take_profit_3", "tp1_share", "tp2_share",
    "tags", "confluence", "reason",
)  # fmt: skip


def _entry(t: TradeResult) -> tuple:
    return tuple(getattr(t, f) for f in ENTRY_FIELDS)


@pytest.mark.parametrize(("name", "label"), CASES)
def test_future_candles_change_no_earlier_result(name, label):
    """A run on a prefix equals the longer run up to the cut: same entries, and every trade
    that closed by the cut is identical (trades still open at the cut end as END_OF_DATA in the
    short run only)."""
    trades = _need_trades(name, label)
    config = configs_for(name)[label]
    series = series_for(name)
    base = _strategy(name, config).base_timeframe
    base_series = next(s for s in series if s.timeframe is base)
    first = base_series.view(0).current.ts
    last = base_series.view(len(base_series) - 1).current.ts
    # cut between trades so both sides have trades; else at 60 % of the data
    cut = trades[len(trades) // 2].entry_time + base.duration
    if not first < cut < last:
        cut = first + (last - first) * 0.6
    short = run(name, config, _prefix(series, cut))
    long_ = list(trades)

    short_entries = [_entry(t) for t in short]
    long_entries = [_entry(t) for t in long_ if t.entry_time <= cut]
    assert short_entries == long_entries, f"{name}: entries before {cut} differ with future data"

    closed_short = [t for t in short if t.exit_time <= cut and t.exit_reason.value != "end_of_data"]
    closed_long = [t for t in long_ if t.exit_time <= cut]
    assert closed_short == closed_long, f"{name}: trades closed before {cut} differ"


@pytest.mark.parametrize(("name", "label"), CASES)
def test_trades_enter_at_the_close_of_their_candle(name, label):
    trades = _need_trades(name, label)
    base = _strategy(name, configs_for(name)[label]).base_timeframe
    for t in trades:
        assert t.entry_time == t.entry_candle + base.duration, f"{name}: entry not at a close"
        assert t.exit_time >= t.entry_time
        assert t.exit_candle >= t.entry_candle


@pytest.mark.parametrize(("name", "label"), CASES)
def test_limit_orders_are_not_decided_from_the_candle_they_fill_in(name, label):
    """A limit order that fills inside the candle just closed (`Order.limit_fill`) must have a
    level the strategy knew BEFORE that candle: feeding a flat candle at the same level (it
    still touches the level) must return the same order. Strategies without limit orders pass
    trivially. Strategy 3 body_end / middle pass (ROADMAP 13.19 not reproduced)."""
    config = configs_for(name)[label]
    series = series_for(name)
    strategy = _strategy(name, config)
    base = strategy.base_timeframe
    seen: list[tuple[datetime, object]] = []
    real = strategy.on_candle

    def recording(now, views):
        orders = real(now, views)
        seen.extend((now, o) for o in orders if o.limit_fill)
        return orders

    strategy.on_candle = recording
    Backtest(strategy, series).run()
    if not seen:
        return
    for now, order in seen[:2]:
        flat = _flatten_candle(series, base, now - base.duration, order.entry)
        again: list = []
        probe = _strategy(name, config)
        real2 = probe.on_candle
        probe.on_candle = lambda n, v, real2=real2, now=now, again=again: _grab(
            real2, n, v, now, again
        )
        cut = _prefix(flat, now)
        Backtest(probe, cut).run()
        same = [o for o in again if o.limit_fill and o.entry == order.entry]
        assert same, (
            f"{name}/{label}: the limit order at {now} (level {order.entry}) disappears when the "
            f"candle it fills in is replaced by a flat candle at that level: the level or the "
            f"order is decided from that candle (lookahead)"
        )


def _grab(real, now, views, at, out):
    orders = real(now, views)
    if now == at:
        out.extend(orders)
    return orders


def _flatten_candle(series, base: Timeframe, ts: datetime, price: float):
    from backtester.core.models import Candle

    out = []
    for s in series:
        candles = list(s.view(len(s) - 1).last(len(s)))
        if s.timeframe is base:
            candles = [
                Candle(c.ts, price, price, price, price, c.volume, c.spread) if c.ts == ts else c
                for c in candles
            ]
        out.append(CandleSeries(s.symbol, s.timeframe, candles))
    return tuple(out)


# --- 3. deterministic -------------------------------------------------------------------------


@pytest.mark.parametrize(("name", "label"), CASES)
def test_two_runs_give_identical_trades(name, label):
    first = trades_of(name, label)
    second = tuple(run(name, configs_for(name)[label]))
    assert first == second


@pytest.mark.parametrize("name", list(REGISTRY))
def test_variants_do_not_depend_on_run_order(name):
    """Config A then B in one process equals B alone (no state kept between strategies)."""
    configs = list(configs_for(name).values())
    if len(configs) < 2:
        # a second, different variant: the same config rebuilt from its settings JSON
        configs.append(from_json(to_json(RunSettings(strategy=configs[0]))).strategy)
    a, b = configs[0], configs[-1]
    alone = run(name, b)
    run(name, a)
    again = run(name, b)
    assert alone == again


# --- 4. R only --------------------------------------------------------------------------------

MONEY_WORDS = {"lot", "lots", "money", "balance", "equity", "usd", "eur", "pnl", "cash", "margin"}


def test_trade_result_has_no_money_fields():
    """Every strategy outputs `TradeResult`s: money, lots and balances belong to `risk/`."""
    for f in fields(TradeResult):
        assert not MONEY_WORDS & set(f.name.lower().split("_")), f"money field {f.name}"


@pytest.mark.parametrize(("name", "label"), CASES)
def test_trades_are_in_r_with_a_stop_and_an_exit_reason(name, label):
    for t in _need_trades(name, label):
        assert t.risk > 0, f"{name}: stop distance must be > 0"
        assert t.exit_reason is not None
        for value in (t.r_gross, t.r_net, t.spread_r, t.commission_r, t.mae_r, t.mfe_r):
            assert isinstance(value, float) and np.isfinite(value)
        assert t.mae_r <= 0 <= t.mfe_r
        assert abs(t.r_gross - sum(p.share * p.r_gross for p in t.parts)) < 1e-9
        long = t.direction.name == "BULLISH"
        assert (t.initial_stop < t.entry) == long, f"{name}: stop on the wrong side"


# --- 5. sweepable settings --------------------------------------------------------------------


def _scalar_fields(config, prefix: str = "") -> list[str]:
    names = []
    for f in fields(config):
        value = getattr(config, f.name)
        if dataclasses.is_dataclass(value) and not isinstance(value, type):
            names += _scalar_fields(value, f"{prefix}{f.name}.")
        else:
            names.append(f"{prefix}{f.name}")
    return names


@pytest.mark.parametrize("name", list(REGISTRY))
def test_every_config_field_can_be_swept(name):
    """`research_grid.valid_names` (what a grid file may set) lists each config field. Mapping
    fields (e.g. per-symbol tables) are listed by their entries, so a field counts when it or its
    entries are listed. Fields in `settings.HIDDEN` are hidden on purpose and exempt."""
    valid = set(valid_names(name))
    for field_name in _scalar_fields(default_config(name)):
        if f"strategy.{field_name}" in HIDDEN:
            continue  # deliberately fixed in the settings menu (settings.HIDDEN), not swept
        listed = field_name in valid or any(v.startswith(f"{field_name}.") for v in valid)
        assert listed, f"{name}: config field {field_name!r} cannot be set from a research grid"


# --- 6. mirror --------------------------------------------------------------------------------


@pytest.mark.skip(reason="no generic mirror test, see the docstring")
def test_mirror_is_not_generic():
    """Mirrored data (price inverted) should give mirrored directions, but no generic test is
    possible: spreads, tick sizes, swing and zone ties and stop buffers are not symmetric on
    inverted prices, and entry rules key on session times, not only on shape. The bullish /
    bearish mirror is tested per detector with hand-built candles (tests/detectors)."""
